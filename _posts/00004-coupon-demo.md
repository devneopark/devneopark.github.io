---
seq: 4
title: "이커머스 선착순 쿠폰 발급 예제: Redis/Kafka 없이 처리량 늘리기"
summary: "선착순 쿠폰 발급 예제에서 인프라 요소를 늘리지 않고 RDB 만으로 동시성 병목을 줄여본 실험입니다."
tags: [ "postgresql", "skip-locked", "concurrency-control", "advisory-lock" ]
posted_at: "2026-04-30"
---

> [예제 코드 보러가기](https://github.com/devneopark/coupon-demo)

# 인프라 다이어트

한때 백엔드 과제전형의 주제로 선착순 쿠폰 발급 과제를 자주 만났었습니다. 동시성 처리가 필요한 대표적인 예제로, 흔히 `Redis`/`분산락`/`메세지 브로커(큐)` 같은 인프라 키워드를 먼저 떠올리곤합니다. 물론, 여러 인프라를 사용할 수 있고 팀에서 관리할 여력이 있는 환경이라면 이런 선택이 필요할 수 있습니다. 하지만 최근 개인적으로 많이 느끼는 부분은 팀 규모가 작거나 인프라 비용이 부담스러운 경우, 특히 개인의 사이드 프로젝트같은 상황에서는 더더욱 인프라 다이어트가 필요하다고 느꼈습니다. ~~_사이드 프로젝트하나에 수십만원 태우면 먹고살기 힘들어요..._~~

이번에 시도해본 방식은, **가능한 작은 인프라 구성으로 어디까지 처리량을 확보할 수 있을까**를 고민해봤습니다. 가용 자원은 서버 애플리케이션 N개가 RDB 인스턴스 한대에 붙는 다고 가정했습니다. **PostgreSQL 안에서 동시성을 처리하고, 잠금 범위를 최대한 좁혀서 동시성 처리 포인트를 분산**하는 전략을 세웠습니다.

# 쿠폰 정의와 재고

선착순 쿠폰 발급 요구사항을 쿠폰 중심으로 보면 보통 `coupon` 테이블에 발급가능한 총량(`total_quantity`)과 남은 수량(`remaining_quantity`)를 둡니다. 사용자가 쿠폰을 발급받으면 남은 수량을 차감하고, 사용자별 발급 수 제한은 이력테이블(`coupon_issue_ledger`)로 관리합니다. 원초적으로 요구사항 구현 자체에 초점을 두면 이 접근도 '맞는'설계고, 비즈니스 로직이 단순해질 수 있습니다. 

```
// 비즈니스로직 pseudo code
@Transactional
func IssueId issue(CouponId couponId, UserId userId) {
  Coupon coupon = couponRepository.쿠폰_조회_WithExclusiveLock(couponId);
  coupon.issue(); // 쿠폰 재고 차감
  ... 쿠폰 히스토리 검증 & 히스토리 레코드 생성 ...
}
```

하지만 쿠폰의 남은 수량을 차감할때 `coupon`테이블의 레코드 자체를 잠가야하고, 발급 트랜잭션이 하나씩 처리되기때문에 처리량은 쿠폰 레코드 갱신 속도에 묶여 병목이 됩니다.

관점을 살짝만 바꿔 '쿠폰 재고' 개념을 추가해보겠습니다. 쿠폰의 정의와 발급 가능한 재고를 분리해서 도메인 모델을 나눕니다.

```
class Coupon { // 쿠폰 정의, 정책
  CouponId id;
  String name;
  int maxIssueCountPerUser;
  ...
}

---

class PreparedCoupon { // 쿠폰 재고, 실제 발급 가능한 단위
  PreparedCouponId id;
  CouponId couponId;
  UserId issuedTo;
  Instant issuedAt;
  ...
}
```

**쿠폰 정의**는 식별자/이름/사용자별 최대 발급 수량과 같은 필드로 쿠폰 정의 자체가 하나의 정책이 됩니다. 관리자가 '봄 시즌오프 30% 할인 쿠폰'을 만들면 그 정의가 Coupon이 됩니다. 사용자가 실제로 발급해서 사용할 쿠폰 자체는 PreparedCoupon이 됩니다. 관리자는 쿠폰을 정의하고 시스템에서 허용할 최대 쿠폰 발급 수 만큼 미리 쿠폰 재고 레코드를 채워둡니다.

> ### 왜 미리 레코드를 만들어 두나요? 저장하지 않아도 될 레코드가 쌓이는것 아닌가요?
> 이커머스 환경에서 선착순 쿠폰 이벤트로 준비한 쿠폰은 대부분 실제 발급될 확률이 높습니다. 어차피 생성될 레코드라면, 미리 재고를 만들어 발급 순간에 계산과 쓰기 부담을 줄이는 방식입니다. 피크시간대 쿠폰 발급시에 고객이 응답을 기다리다가 타임아웃을 만나면 서비스 UX에 훨씬 더 큰 비용을 만듭니다.  
> 또, 재고 레코드는 굉장히 작은 데이터입니다. 10개 이하 필드 레코드 수십만여건을 며칠 ~ 몇 주 더 보관하는 비용은 Redis/Kafka 같은 인프라 비용보다 훨씬 더 예측 가능하고 저렴할 수 있습니다. 인프라 요소에 들어가는 클라우드 리소스 비용 + 인건비 + @ 보다 충분히 지불할만한 비용이라고 볼 수 있습니다.

```
SELECT ...
FROM prepared_coupon p
WHERE p.coupon_id = :couponId AND p.issued_to IS NULL
ORDER BY p.id
LIMIT 1
FOR UPDATE
SKIP LOCKED
```

쿠폰 정의와 재고를 분리하고 `SKIP LOCKED` 기능을 사용합니다. 아직 발급되지 않은 상태의 재고 레코드 중 이미 잠겨있는 레코드는 건너뛰고 다음 레코드 하나를 선점하는 방식으로, 잠금 범위가 쿠폰 전체에서 재고 레코드 하나로 줄어듭니다.

본격적으로 발급 쿠폰을 발급하는 유즈케이스 트랜잭션의 핵심은

```
@Transactional
func PreparedCoupon issue(UserId userId, CouponId couponId) {
  1. 쿠폰 정의 조회
  2. 쿠폰 재고 선점
  3. 쿠폰 발급 처리
}
```

순으로 처리됩니다. 한가지 디테일을 추가하자면, 앞서 언급한 사용자별로 발급 수량을 제한하는 로직입니다. `coupon_issue_count` 테이블을 추가로 두고, 사용자 + 쿠폰 조합별 발급 횟수를 기록하게 했습니다.

```
class CouponIssueCount { // 사용자 + 쿠폰 조합별 발급 횟수
  CouponIssueCountId id; // couponId + userId 복합키
  int count;
}
```

사용자 + 쿠폰 조합별 발급 횟수를 기록할때도 동시성 처리가 필요한데, 여기서는 advisory lock을 사용합니다. 쿠폰 A를 사용자 1이 처음 발급하는 상황이라면 `FOR UPDATE`로 잠글 레코드 자체가 없습니다. 동시성 이슈에 대해 보수적으로 접근한다면 advisory lock으로 사용자 + 쿠폰 조합을 잠그고 카운트 레코드는 upsert 하는 방식이 좀 더 나은 선택지라고 판단했습니다.

```
SELECT 1 FROM pg_advisory_xact_lock(hashtext(:couponId), hashtext(:userId))
```

> MySQL에서는 `named_lock`기능으로 거의 동일한 동작을 수행할 수 있습니다.

유즈케이스 트랜잭션을 정리하면 이렇게 됩니다.

```
@Transactional
func PreparedCoupon issue(UserId userId, CouponId couponId) {
  1. 쿠폰 정의 조회
  2. 쿠폰 재고 선점
  3. 쿠폰 + 사용자 조합으로 애플리케이션 레벨 잠금 선점
  4. 발급 카운트 레코드 upsert
  5. 쿠폰 발급 처리
}
```

# 벤치마크

코드상으론 병목을 줄인다고 '주장'하지만, 실제로 어느정도 차이가 나는지 감을 잡기위해 로컬환경에서 간단히 테스트 해봤습니다.

테스트 조건:

동시요청수 = 10,000
재고 = 10,000
스레드수 = 200

비교대상:

- prepared_coupon + FOR UPDATE SKIP LOCKED
    - 미리 준비된 쿠폰 재고 레코드 중 하나를 선점
    - 각 요청이 서로 다른 prepared_coupon 행을 잠글 수 있음
- coupon.remaining_count 단일 행 갱신
    - coupon 레코드에 remaining_count 필드를 둠
    - 발급 요청마다 같은 coupon 행의 remaining_count를 차감

결과:

- prepared_coupon + FOR UPDATE SKIP LOCKED

```
[prepared_coupon_skip_locked]
  requests=10000
  stock=10000
  threads=200
  success=10000
  failure=0
  elapsed=4,670ms
  throughput=2,141.07/s
```

- coupon.remaining_count 단일 행 갱신

```
[coupon_remaining_count]
  requests=10000
  stock=10000
  threads=200
  success=10000
  failure=0
  elapsed=15,105ms
  throughput=662.02/s
```

물론 이 결과만으로 “항상 3배 빠르다”고 말할 수는 없습니다. 실제 수치는 DB 스펙, 커넥션 풀 크기, 인덱스, 트랜잭션 안에서 수행하는 비즈니스 로직, 네트워크 지연, 컨테이너 환경 등에 따라 달라집니다. 하지만 적어도 이번 테스트에서는 병목의 위치가 명확하게 보였습니다.

# 사고의 전환

처음에 선착순 쿠폰발급이라 하면 쿠폰 단일 레코드 잠금 -> 인프라 확장으로 생각을 이어가기 쉽습니다. 처음에는 병목을 인프라 요소로 해결하는 방향을 고려했었지만 이번에는 반대로 생각해봤습니다. "병목이 생기니 인프라를 붙이자"가 아니라, "왜 병목이 한쪽으로 집중되나?"에 포인트를 두고 생각해봤습니다. 이번에 재고 모델을 도입하면서 느낀점은 '동시성 문제를 항상 외부 시스템으로 밀어내지 않아도 된다'입니다. 때로는 이번 예제처럼 도메인 개념을 좀 더 잘게 나누고, 기존 인프라의 기능을 적절히 사용해 단순한 구성으로도 요구사항을 만족할 수 있게 할 수 있었습니다.

물론 이 방식이 '은탄환'이 될수는 없습니다. 발급 처리과정을 대기열에 태워 비동기로 처리해야하거나, 트래픽 규모가 훨씬 크다면 다른 인프라 요소를 도입하는것이 더 적절할 수 있습니다. Kafka 클러스터를 붙이고, 운영/모니터링/장애에 대응하는 비용은 생각보다 큽니다. 이번처럼 사이드 프로젝트나 초기 서비스처럼 인프라 관리비용이 곧 개발 비용이 되는 환경이라면 선택지를 달리 해야할 수 있습니다. 

선착순 쿠폰 발급이라는 흔한 문제도 관점을 살짝만 바꿔보면 꽤 다른 설계가 나올 수 있다는걸 이번 시도로 알게됐습니다.
