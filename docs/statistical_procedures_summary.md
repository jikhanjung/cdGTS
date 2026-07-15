# Agterberg, Hammer & Gradstein (2012), *Statistical Procedures* 요약

> **성격**: 외부 문헌 요약(참고자료). 개념 코퍼스가 아니라 읽기 노트이므로 한국어 단독(EN 쌍 없음).
> **출처**: Agterberg, F.P., Hammer, O. & Gradstein, F.M. (2012). *Statistical Procedures*.
> In *The Geologic Time Scale 2012*, Chapter 14, pp. 269–273.
> **자매 문서**: [radiogenic_isotope_geochronology_summary.md](radiogenic_isotope_geochronology_summary.md) —
> 같은 책 Chapter 6(Schmitz, *Radiogenic Isotope Geochronology*). 본 문서 §16.5(internal vs external error,
> duration vs 절대연대)가 명시적으로 그 장의 오차 논의를 가리킨다. 두 문서는 한 쌍으로 읽는 것이 좋다.
>
> ⚠️ **§1–20 은 챕터 요약, §21–26 은 cdGTS 관점의 해석·확장이다** — 원저의 주장이 아니다.
> 특히 §26(향후 개선 가능성)은 저자들의 로드맵이 아니라 이 저장소 관점에서 덧붙인 것이므로,
> 인용할 때 Agterberg et al. 의 말로 옮기지 말 것.

## 한 문장 요약

이 장은 지질시대 경계의 수치 연대를 계산하기 위해 **방사성동위원소 연대와 상대 층서 위치를 cubic smoothing spline으로 연결하고, 방사성연대 오차와 층서 위치 오차를 함께 반영하며, Monte Carlo 반복계산으로 Stage·biozone 경계 연대의 신뢰구간을 추정하는 방법**을 설명한다. GTS2012의 시간척도는 개별 연대값을 단순 평균한 결과가 아니라, 불규칙하게 분포한 연대자료를 층서 순서에 맞춰 보간한 통계적 age model이다.

---

## 1. 이 장의 목적

수치 지질연대표를 만들 때 입력자료는 대체로 다음과 같다.

- 방사성동위원소 연대
- 각 연대의 분석오차
- 시료의 층서 위치
- 시료가 속한 biozone 또는 여러 zone 범위
- 상대적 생층서 척도
- magnetostratigraphy 또는 spreading-distance scale

문제는 이 자료가 다음과 같은 특성을 가진다는 점이다.

```text
연대값:
불규칙하게 분포

오차:
시료마다 다름

층서 위치:
정확한 층준 또는 넓은 zone 범위

목표:
모든 Stage·zone 경계에 연대와 오차 부여
```

따라서 단순 선형보간이나 평균으로는 충분하지 않다.

이 장의 기본 접근은 다음과 같다.

```text
방사성연대
+ 상대 층서 위치
+ 두 축의 불확실성
→ smoothing spline
→ 경계 연대 보간
→ Monte Carlo
→ 95% 신뢰구간
```

---

# 2. 지질연대표 계산의 역사

## 2.1 기존 방법

과거 지질연대표에서는 Stage 경계 연대를 계산하기 위해 다음 방법이 사용되었다.

- chronogram
- maximum likelihood
- graphical calibration
- curve fitting
- cubic smoothing spline
- 전문가의 주관적 판단

이 방법들은 각각 다음 문제를 해결하려 했다.

- 경계 위·아래의 상충하는 연대
- 분석오차가 서로 다른 자료
- 시료의 부정확한 층서 위치
- 구간마다 다른 퇴적률
- 불규칙한 연대자료 분포

---

## 2.2 Chronogram method

Harland 등의 time scale에서 사용한 chronogram 방법은 하나의 Stage 경계에 여러 후보 연대를 넣어 보면서, 그 경계와 모순되는 방사성연대의 정도를 계산한다.

가상의 경계 연대를 \(T\)라고 하면:

- 경계 위의 시료는 \(T\)보다 젊어야 함
- 경계 아래의 시료는 \(T\)보다 오래되어야 함

모순되는 연대는 다음과 같다.

```text
경계 위 시료인데 trial age보다 오래됨
또는
경계 아래 시료인데 trial age보다 젊음
```

각 모순의 크기는 연대의 표준편차로 나누어 표준화한다.

\[
z_i = \frac{\text{관측 연대} - \text{trial age}}{\sigma_i}
\]

그 제곱합:

\[
E^2 = \sum z_i^2
\]

을 여러 trial age에 대해 계산한다.

Chronogram은 \(E^2\)를 trial age에 대해 그린 U자형 곡선이며, 최소값을 만드는 연대를 최적 경계연대로 선택한다.

---

## 2.3 Chronogram의 가정

이 방법에는 다음 가정이 있다.

1. 시료가 시간축에 대체로 균일하게 분포한다.
2. 연대오차는 Gaussian distribution을 따른다.
3. 보고된 표준편차가 실제 분석오차를 잘 나타낸다.
4. 경계 위·아래의 상대 위치가 정확하다.
5. Stage 내부의 세부 층서 위치는 중요하지 않다.

마지막 가정은 중요한 약점이다.

Chronogram은 시료가 Stage의 상부인지 하부인지, 같은 Stage 안에서 다른 시료보다 얼마나 위에 있는지를 충분히 사용하지 않는다.

---

## 2.4 Maximum likelihood 개선

Agterberg는 모순되는 자료뿐 아니라 trial age와 일관적인 자료도 함께 사용하는 maximum likelihood 접근을 제안했다.

각 연대와 trial age의 차이를 정규분포 확률로 바꾸고, 모든 확률의 로그를 합산한다.

```text
trial age
→ 각 연대와의 standardized difference
→ normal probability
→ log-likelihood 합산
→ 최대 likelihood의 age 선택
```

log-likelihood curve는 벌집 모양의 단봉 곡선이 된다.

하지만 실제로는 모순되는 연대가 더 큰 정보량을 가지므로, consistent date를 추가해도 개선 폭이 크지 않은 경우가 많다.

자료 수가 적을 때에는 consistent date를 포함하는 것이 더 중요하다.

---

# 3. 상대 층서 위치의 중요성

## 3.1 Stage 단위 정보의 한계

하나의 시료가 단순히 “Middle Ordovician”에 속한다는 것보다 다음 정보가 더 유용하다.

```text
특정 conodont zone의 하부
특정 graptolite zone의 상부
두 bioevent 사이 35% 지점
```

정밀한 방사성연대가 소수뿐일수록, 각 시료의 상대 층서 위치를 가능한 한 자세히 활용해야 한다.

---

## 3.2 McKerrow 방식

McKerrow 등은 방사성연대를 x축, 상대 층서척도를 y축에 놓고 두 관계를 반복적으로 조정했다.

이 방법에서 y축은 처음부터 수치 시간이 아니다.

```text
x축:
방사성연대 Ma

y축:
Period–Stage–biozone의 상대적 순서
```

목표는 분석오차와 층서오차를 나타내는 사각형들을 가능한 한 잘 통과하는 직선 또는 곡선을 만드는 것이다.

---

## 3.3 Cooper의 Ordovician time scale

Cooper는 고정밀 TIMS U–Pb zircon 연대 14개와 Sm–Nd 연대 1개를 이용하여 Ordovician 상대 시간척도를 조정했다.

절차는 다음과 같았다.

```text
biozone 기반 상대 척도
→ 방사성연대와 비교
→ 구간별 상대길이를 늘리거나 줄임
→ 직선회귀와 최적 적합
```

이 방식은 퇴적률 비교와 경험적 재비례에 일부 의존했다.

Agterberg는 이 자료에 spline fitting을 적용했으며, 최적 smoothing이 거의 직선에 가까움을 보였다.

---

# 4. GTS2004의 spline fitting

## 4.1 기본 입력

GTS2004의 방법은 다음 입력으로 시작한다.

```text
(x_i, y_i)
```

여기서:

- \(x_i\): 상대 층서 위치
- \(y_i\): 방사성연대 Ma
- \(\sigma_x\): 층서 위치 오차
- \(\sigma_y\): 연대 분석오차

목표는 다음 함수를 추정하는 것이다.

\[
y = f(x)
\]

즉:

```text
상대 층서 위치
→ 수치 연대
```

를 변환하는 age model이다.

---

## 4.2 Cubic smoothing spline

Cubic smoothing spline은 모든 점을 정확히 통과하는 interpolation curve와 완전히 직선적인 regression 사이의 절충이다.

```text
smoothing이 약함
→ 자료점을 자세히 따라감
→ 곡선이 요동할 수 있음

smoothing이 강함
→ 부드러운 곡선
→ 국지적 변화가 사라질 수 있음
```

Spline은 다음을 동시에 고려한다.

- 자료와 곡선 사이의 잔차
- 곡선의 부드러움
- 각 연대의 오차
- 필요하면 층서 위치 오차

---

## 4.3 상대 층서척도의 조건

초기 상대척도는 시간에 대략 비례해야 한다.

이상적인 경우:

```text
relative stratigraphic scale
≈ numerical time scale의 선형변환
```

과거에 사용된 덜 만족스러운 가정은 다음과 같다.

- 모든 Stage의 지속시간이 같음
- 모든 biozone의 지속시간이 같음
- 보정된 퇴적률이 시간에 비례함

이런 척도도 출발점으로 사용할 수 있지만, 초기척도가 최종 spline의 형태에 일부 영향을 줄 수 있다.

---

# 5. 두 축의 오차

## 5.1 방사성연대 오차

각 연대는 발표된 1σ 또는 2σ 오차를 가진다.

Spline fitting에서는 일반적으로 분산의 역수를 가중치로 사용한다.

\[
w_i = \frac{1}{\sigma_i^2}
\]

따라서:

```text
정밀한 연대
→ 높은 가중치

불확실한 연대
→ 낮은 가중치
```

를 가진다.

---

## 5.2 층서 위치 오차

시료의 층서 위치도 불확실할 수 있다.

예:

- 하나의 biozone 안 어디인지 불명확
- 두 개 이상의 zone 범위에서만 알려짐
- 원래 논문의 상관이 불확실
- 화산재층의 정확한 위치가 모호함

Paleozoic 자료에서는 층서 위치 오차가 방사성연대 오차보다 클 수도 있다.

---

## 5.3 층서 오차의 rectangular distribution

분석오차는 Gaussian distribution으로 모델링할 수 있지만, 층서 위치 오차는 보통 rectangular distribution이 더 적절하다.

예를 들어 시료가 특정 zone 어디엔가 있다는 정보만 있다면:

```text
zone 하부, 중부, 상부
→ 모두 같은 확률
```

이라고 보는 것이다.

층서 오차 범위의 전체 길이를 \(q\)라고 할 때 rectangular distribution의 분산은:

\[
\mathrm{Var}(x) = \frac{q^2}{12}
\]

표준편차는:

\[
\sigma_x = \frac{q}{\sqrt{12}}
\]

본문에서는 이를 다음과 같은 형태로 표현한다.

\[
\sigma(x) = 1.15q/4
\]

이는 Gaussian error bar와 rectangular stratigraphic range를 구분하기 위한 처리다.

---

## 5.4 두 오차의 결합

층서 위치오차와 연대오차를 결합하려면 두 값이 같은 단위여야 한다.

즉, 상대 층서 위치의 오차도 Ma로 환산해야 한다.

총 분산은 근사적으로 다음과 같이 다룬다.

\[
\sigma_t^2
=
\sigma_x^2 + \sigma_y^2
\]

다만 \(\sigma_x\)는 층서척도를 시간에 비례하도록 변환한 뒤 계산해야 한다.

---

## 5.5 층서척도를 Ma에 맞추기

상대척도의 최고·최저 위치 차이를 가장 오래된 연대와 가장 젊은 연대의 Ma 차이에 대응시킨다.

```text
relative scale range
↔
observed age range
```

이렇게 하면 상대 위치오차를 대략 Ma 단위로 환산할 수 있다.

이 방법은 spline이 대체로 직선에서 크게 벗어나지 않는다는 경험적 특성에 기반한다.

---

# 6. Smoothing factor

## 6.1 정의

Spline은 smoothing factor, SF에 의해 곡선의 부드러움이 결정된다.

각 점의 scaled residual은:

\[
r_i =
\frac{y_i-f(x_i)}
{\sigma_i}
\]

이다.

SF는 scaled residual 제곱평균의 제곱근과 관련된다.

오차가 올바르게 평가되었다면 일반적으로:

```text
SF ≈ 1
```

이어야 한다.

---

## 6.2 SF의 해석

### SF가 약 1

보고된 오차와 자료의 산포가 대체로 일치한다.

### SF가 1보다 현저히 큼

- 보고된 오차가 지나치게 작음
- 자료 사이에 설명되지 않는 불일치가 있음
- 일부 연대가 과도하게 정밀하게 보고됨
- 층서 상관오차가 누락됨

### SF가 1보다 작음

보고된 오차가 다소 보수적이거나, 자료가 매우 부드러운 관계를 보일 수 있다.

Paleozoic 자료에서는 최적 SF가 1보다 작은 경우가 흔했다.

---

# 7. Leave-one-out cross-validation

## 7.1 목적

SF를 연구자가 임의로 정하지 않고 자료 자체에서 선택하기 위해 cross-validation을 사용한다.

---

## 7.2 절차

각 연대를 하나씩 제외한다.

```text
연대 i 제외
→ 나머지 자료로 spline 계산
→ 제외된 x_i 위치에서 연대 예측
→ 실제 y_i와 차이 계산
```

모든 내부 자료점에 대해 이를 반복한다.

각 SF 후보에 대해 예측오차 제곱합을 계산한다.

\[
CV(SF)
=
\sum
\left(
y_i-\hat{y}_{-i}(x_i)
\right)^2
\]

가장 작은 CV 값을 만드는 SF를 선택한다.

---

## 7.3 실제 영향

최적 SF가 1과 다르더라도 최종 spline 곡선 자체는 크게 달라지지 않는 경우가 많다.

즉, cross-validation은 모델 선택의 객관성을 높이지만, 대부분의 자료에서는 SF=1과 비교해 경계연대가 크게 바뀌지는 않는다.

---

# 8. Figure 14.1

Figure 14.1은 Cambrian–Ordovician 경계 부근의 소규모 자료를 이용해 spline과 Monte Carlo 과정을 보여준다.

### 검은 점과 곡선

- 실제 입력 연대
- 층서 위치 error bar
- 방사성연대 2σ error bar
- cross-validation으로 선택된 spline

실제 자료 spline에서 Cambrian–Ordovician 경계는:

```text
485.39 Ma
```

로 계산된다.

### 파란색·초록색 점과 곡선

입력 오차분포에서 무작위로 생성한 Monte Carlo replicate다.

각 replicate마다:

- 연대값이 달라짐
- 층서 위치가 달라짐
- 최적 SF가 달라짐
- spline이 다시 계산됨
- 경계연대가 다시 계산됨

예시 replicate 경계연대:

- 485.17 Ma
- 487.06 Ma

이 그림은 하나의 입력자료 세트에서 계산한 단일 경계연대보다, 반복 가능한 결과분포가 더 중요하다는 점을 보여준다.

---

# 9. Spline의 지질학적 의미

## 9.1 직선으로부터의 편차

초기 상대척도가 실제 시간에 완전히 비례하지 않으면 spline은 직선이 아니다.

곡선의 기울기 변화는 다음을 반영할 수 있다.

- 퇴적률 변화
- biozone 지속시간 변화
- 진화속도 변화
- composite scale의 비선형성
- 잘못된 초기 time allocation

따라서 spline은 단순한 수학적 보간만이 아니라, 초기 상대척도의 왜곡을 교정한다.

---

## 9.2 Smoothness assumption

이 방법은 절대시간이 상대 층서 위치의 부드러운 함수라고 가정한다.

```text
age = smooth function of stratigraphic position
```

그러나 다음 상황에서는 이 가정이 깨질 수 있다.

- global hiatus
- 큰 부정합
- 급격한 퇴적률 변화
- composite scale의 큰 결손
- 잘못된 bioevent 순서
- 실제 time gap이 포함된 zone

이 경우 spline은 hiatus를 부드럽게 보간해 실제보다 연속적인 시간축을 만들 수 있다.

---

# 10. Outlier 처리

## 10.1 왜 outlier가 발생하는가

Spline에서 크게 벗어나는 연대는 다음 문제를 가질 수 있다.

- 분석오차 과소평가
- Pb loss
- inherited zircon
- alteration
- 잘못된 표준
- 잘못된 층서 위치
- 잘못된 biozone 상관
- 재퇴적된 화산재
- 통계적 우연

이 장의 절차는 outlier를 즉시 삭제하지 않고, 우선 해당 연대의 표준편차가 과소평가되었다고 본다.

---

## 10.2 scaled residual test

각 자료점의 scaled residual:

\[
z_i =
\frac{y_i-f(x_i)}{\sigma_i}
\]

은 표준정규분포를 따라야 한다.

그 제곱:

\[
z_i^2
\]

은 자유도 1의 chi-square distribution을 따른다.

따라서 잔차가 해당 error bar로 설명 가능한지 확률검정을 할 수 있다.

---

## 10.3 오차 조정

확률이 너무 작으면:

```text
p < 0.05
```

그 연대의 표준편차가 지나치게 작다고 판단한다.

절차는 해당 확률을 0.5에 해당하도록 오차를 확대하는 것이다.

자유도 1의 chi-square에서 중앙값에 대응하는 값은 약:

\[
\chi^2 = 0.4549
\]

이며:

\[
Z = 0.674
\]

에 해당한다.

새로운 표준편차는 기존 scaled residual을 0.674로 나누는 방식으로 확대된다.

이후 spline을 다시 계산한다.

---

## 10.4 의미

이 방식은 다음과 다르다.

```text
outlier 삭제
```

대신:

```text
outlier의 영향력 감소
```

를 수행한다.

즉, 자료는 유지하되 가중치를 낮춘다.

하지만 지질학적 원인이 명백한 경우에는 단순한 통계적 오차 확대보다 시료 재검토가 우선되어야 한다.

---

# 11. Zone·Stage 경계연대 계산

Spline이 완성되면 zone 또는 Stage 경계의 상대 위치 \(x_b\)에서 연대를 보간한다.

\[
t_b = f(x_b)
\]

Zone의 지속시간은 두 경계연대 차이로 계산한다.

\[
D =
t_{\mathrm{older}}
-
t_{\mathrm{younger}}
\]

---

# 12. GTS2004의 경계오차 계산

GTS2004에서는 spline을 “rectify”한 뒤 MLFR regression으로 경계오차를 추정했다.

대략적인 절차:

```text
원 방사성연대
↔
spline predicted age

→ 직선회귀
→ slope와 intercept 오차
→ residual standard deviation
→ zone boundary error
→ smoothing/ramping
```

이 방법은 spline이 층서척도와 시간 관계의 기울기 변화를 정확히 보정했다는 가정에 의존했다.

---

# 13. GTS2012의 수정

## 13.1 무엇이 달라졌는가

GTS2012에서는 spline fitting 자체는 크게 바뀌지 않았다.

주요 변화는 다음이다.

- 새로운 연대자료 추가
- 새로운 층서정보 반영
- GTS2004 또는 갱신된 상대척도를 입력으로 사용
- Stage boundary error bar 계산법 변경

즉, 새로운 연대값의 변화는 통계 방법 자체보다 **업데이트된 입력자료와 새 spline**에서 주로 발생했다.

---

# 14. Monte Carlo confidence interval

## 14.1 핵심 질문

GTS2012의 질문은 다음과 같다.

> 동일한 시료를 다시 채취하고 연대를 다시 측정하고, 층서 위치를 다시 추정하고, spline fitting을 반복한다면 경계연대는 얼마나 달라질 것인가?

이를 직접 실험할 수 없으므로 Monte Carlo simulation으로 근사한다.

---

## 14.2 Monte Carlo 절차

각 replicate에서:

1. 각 방사성연대의 정규분포에서 무작위 연대 생성
2. 각 층서 위치의 rectangular distribution에서 무작위 위치 생성
3. 생성된 자료로 cross-validation 수행
4. 최적 SF 선택
5. spline 재계산
6. Stage·zone 경계연대 보간
7. 결과 저장

이를 예를 들어:

```text
10,000회
```

반복한다.

---

## 14.3 결과

각 경계에 대해 10,000개의 연대가 생성된다.

```text
boundary age distribution
→ histogram
→ 2.5 percentile
→ 97.5 percentile
→ 95% confidence interval
```

이 방식은 GTS2004의 간접 regression 방식보다 직관적이며, 입력 오차가 경계연대로 어떻게 전파되는지 직접 모사한다.

---

## 14.4 계산량

각 Monte Carlo replicate 안에서도 최적 SF를 찾기 위한 여러 spline 계산이 필요하다.

```text
10,000 replicates
×
multiple trial smoothing factors
×
leave-one-out fits
```

따라서 계산량이 크다.

---

# 15. Monotonicity constraint

## 15.1 time reversal 문제

일부 Monte Carlo replicate에서는 극단적인 무작위 조합 때문에 spline이 심하게 구부러질 수 있다.

그 결과:

```text
위로 갈수록 지층이 더 오래되는 구간
```

즉, time reversal이 발생할 수 있다.

이는 층서학적으로 불가능하다.

---

## 15.2 해결 방법

GTS2012에서는 spline이 단조 증가 또는 단조 감소하도록 smoothing factor를 자동으로 높인다.

```text
non-monotonic spline
→ SF 증가
→ 더 부드러운 spline
→ time reversal 제거
```

이는 다음 제약을 적용한 것이다.

```text
층서 순서
→ 시간 순서와 일치
```

---

# 16. Monte Carlo 방식의 한계

## 16.1 replicate 중심값 문제

Monte Carlo 분포는 실제의 알려지지 않은 참값이 아니라, 관측된 연대값을 중심으로 생성된다.

즉:

```text
true population mean
≠ 반드시 observed date
```

인데도 observed date를 평균으로 사용한다.

이 근사가 confidence interval에 얼마나 영향을 주는지는 본문에서 충분히 조사되지 않았다.

---

## 16.2 Smoothness violation

실제 시간–층서 관계에 큰 hiatus가 있으면 smooth spline 가정이 틀린다.

이 경우 Monte Carlo 신뢰구간은 모델오차를 충분히 포함하지 못한다.

```text
reported confidence interval
=
measurement + stratigraphic uncertainty

하지만
model structural error는 일부 누락
```

---

## 16.3 독립오차 가정

Monte Carlo는 모든 방사성연대 오차가 독립적이라고 가정한다.

하지만 실제 geochronology의 오차는 다음으로 나뉜다.

### Internal error

- 측정통계
- blank
- grain-to-grain scatter
- 한 분석 안에서 독립적인 성분

### External error

- decay constant
- tracer calibration
- monitor standard
- laboratory-scale calibration
- method-wide systematic uncertainty

External error는 여러 시료에 공통으로 작용하므로 서로 강하게 상관되어 있다.

---

## 16.4 경계연대 오차의 과소평가

모든 오차를 독립적으로 취급하면 systematic error가 반복계산에서 평균적으로 상쇄되는 것처럼 보일 수 있다.

실제로는 같은 방향으로 함께 움직인다.

따라서 Stage boundary의 절대연대 오차는 일부 과소평가될 수 있다.

---

## 16.5 Duration 오차

Stage 지속시간은 상·하부 경계의 차이다.

공통 external error는 두 경계를 대체로 같은 방향으로 이동시키므로 지속시간에는 크게 기여하지 않는다.

따라서 duration error를 계산할 때는 internal error만 사용하는 것이 더 적절하다.

```text
absolute boundary age:
internal + external error 중요

duration:
주로 internal error 중요
```

이 구별은 Chapter 6의 방사성동위원소 연대오차 논의와 직접 연결된다.

---

# 17. 적용 구간

이 방법은 다음 자료에 적용되었다.

- Ordovician–Silurian
- Devonian
- Upper Cretaceous
- Paleogene

Paleozoic에서는 상대 생층서척도와 방사성연대를 연결했다.

Paleogene의 일부에서는 상대 층서 위치 대신 South Atlantic spreading center로부터의 거리를 사용했다.

```text
distance from spreading center
→ relative time coordinate
→ radiometric calibration
→ polarity boundary ages
```

이 경우 층서 위치 오차는 무시할 수 있다고 보았다.

---

# 18. 강점

## 18.1 자료의 불규칙성 처리

방사성연대가 균일한 간격으로 분포하지 않아도 사용할 수 있다.

---

## 18.2 두 종류의 오차 반영

- 수치 연대 오차
- 층서 위치 오차

를 함께 고려한다.

---

## 18.3 가중치

정밀한 연대가 더 큰 영향을 갖고, 불확실한 연대는 작은 영향을 갖는다.

---

## 18.4 비선형 시간척도

biozone이나 상대척도가 실제 시간에 완전히 비례하지 않아도 spline이 이를 보정할 수 있다.

---

## 18.5 Outlier 완화

이상값을 단순 삭제하지 않고 오차를 조정하여 가중치를 낮춘다.

---

## 18.6 경계연대와 신뢰구간

모든 zone·Stage 경계에 연대와 95% confidence interval을 부여할 수 있다.

---

## 18.7 재현 가능성

입력자료와 알고리즘이 공개되면 같은 time scale을 재계산할 수 있다.

---

# 19. 주요 한계

1. 초기 상대 층서척도가 최종 spline에 영향을 준다.
2. 절대시간이 층서 위치의 smooth function이라는 가정이 필요하다.
3. 큰 hiatus를 부드럽게 보간할 수 있다.
4. rectangular stratigraphic error는 단순화된 가정이다.
5. 층서 위치오차를 Ma로 변환하는 과정이 근사적이다.
6. outlier의 원인을 단순 오차 과소평가로 취급할 수 있다.
7. 모든 방사성연대 오차의 독립성 가정이 현실적이지 않다.
8. external systematic error 때문에 경계연대 오차가 과소평가될 수 있다.
9. Monte Carlo replicate는 관측값을 참 평균처럼 사용한다.
10. cross-validation으로 SF를 결정해도 모델구조의 불확실성은 반영하지 않는다.
11. 단조 spline 제약은 물리적으로 필요하지만 curve shape에 영향을 준다.
12. 입력 연대의 taxonomic·stratigraphic 오류는 통계적으로 자동 해결되지 않는다.
13. spline은 인과모델이 아니라 경험적 보간모델이다.

---

# 20. 핵심 구별

## 측정 연대와 경계 연대

```text
radiometric age
≠ stage-boundary age
```

경계연대는 여러 연대와 층서 위치를 spline으로 보간한 파생값이다.

---

## 분석오차와 층서오차

```text
analytical uncertainty
≠ stratigraphic-position uncertainty
```

두 오차의 분포와 의미가 다르다.

---

## 절대연대 오차와 duration 오차

```text
boundary absolute age error
→ external systematic error 중요

duration error
→ common external error가 상당 부분 상쇄
```

---

## Outlier와 잘못된 자료

큰 잔차가 있다는 사실만으로 자료가 잘못되었다고 단정할 수 없다.

```text
outlier
→ analytical issue?
→ stratigraphic misplacement?
→ model failure?
→ true geological discontinuity?
```

여러 가능성을 검토해야 한다.

---

## Confidence interval과 model uncertainty

Monte Carlo interval은 입력자료의 오차전파를 반영하지만, smooth spline이라는 모델 자체가 틀릴 가능성을 완전히 포함하지 않는다.

---

# 21. cdGTS 관점에서의 데이터 모델링

단순히 다음 최종값만 저장해서는 충분하지 않다.

```text
Cambrian–Ordovician boundary
= 485.39 ± 0.xx Ma
```

최소한 다음 요소를 분리해야 한다.

```text
Radiometric analysis
├─ sample
├─ mineral
├─ isotope system
├─ measured age
├─ internal error
├─ external error
├─ standard
└─ laboratory

Stratigraphic placement
├─ section
├─ numerical level
├─ biozone
├─ lower bound
├─ upper bound
├─ placement distribution
└─ confidence

Relative scale
├─ graphic correlation
├─ CONOP composite
├─ stacked biozones
├─ magnetochron distance
├─ scale units
└─ version

Spline model
├─ input dataset
├─ coordinate transformation
├─ weighting rule
├─ smoothing factor
├─ cross-validation method
├─ monotonicity constraint
└─ model version

Outlier treatment
├─ residual
├─ chi-square probability
├─ original uncertainty
├─ adjusted uncertainty
├─ reason
└─ retained/excluded status

Boundary interpolation
├─ boundary position
├─ spline-predicted age
├─ Monte Carlo distribution
├─ 95% interval
└─ number of replicates

Duration
├─ older boundary
├─ younger boundary
├─ internal-error model
└─ confidence interval
```

---

# 22. 관찰과 계산결과의 분리

## 방사성연대는 입력자료

```text
sample age measurement
```

이다.

## spline은 변환 모델

```text
relative stratigraphic position
→ numerical age
```

이다.

## Stage 경계연대는 파생결과

```text
boundary position
+ spline model
→ interpolated age
```

이다.

이 세 층을 분리해야 한다.

---

# 23. 모델 버전

새로운 방사성연대가 추가되면 spline 전체가 달라질 수 있다.

```text
new high-precision date
→ input dataset update
→ SF cross-validation rerun
→ spline refit
→ all zone boundary ages recalculated
→ all durations recalculated
→ new time-scale version
```

따라서 경계연대를 고정 속성으로 저장하기보다 특정 model version의 결과로 저장해야 한다.

---

# 24. 불확실성의 계층

cdGTS에서는 최소한 다음 오차를 구분하는 것이 좋다.

```text
Measurement uncertainty
├─ internal
└─ external

Stratigraphic uncertainty
├─ exact level
├─ zone interval
└─ correlation uncertainty

Model uncertainty
├─ relative scale
├─ smoothing factor
├─ monotonicity
├─ hiatus
└─ interpolation method

Output uncertainty
├─ boundary age interval
└─ duration interval
```

---

# 25. Monte Carlo를 그래프로 표현하기

```text
Boundary age result
├─ derived from spline model
├─ based on 10,000 replicates
├─ each replicate samples radiometric error
├─ each replicate samples stratigraphic range
├─ each replicate cross-validates SF
├─ each replicate enforces monotonicity
└─ summarized by median and 95% interval
```

이런 구조를 저장하면 경계오차가 어디서 왔는지 추적할 수 있다.

---

# 26. 향후 개선 가능성

이 장의 방법을 현대적으로 확장한다면 다음이 가능하다.

- correlated external error를 covariance matrix로 처리
- Bayesian hierarchical model
- hiatus를 명시적으로 포함한 piecewise age model
- monotonic Gaussian process
- alternative relative-scale ensemble
- robust regression
- explicit outlier mixture model
- joint uncertainty in taxonomy and correlation
- posterior distribution of all boundary ages
- reproducible code와 complete provenance

특히 Chapter 3에서 논의한 composite biochronology와 결합하면 다음 구조가 가능하다.

```text
occurrence data
→ probabilistic event ordering
→ relative biochronology
→ radiometric calibration
→ monotonic age model
→ posterior boundary ages
```

---

## 결론

Agterberg, Hammer와 Gradstein의 Chapter 14는 GTS의 수치연대가 어떻게 통계적으로 만들어지는지를 설명한다.

핵심 과정은 다음과 같다.

```text
정밀하지만 불규칙한 방사성연대
+ 불완전한 층서 위치
+ 상대 biochronologic scale
→ weighted cubic smoothing spline
→ outlier uncertainty adjustment
→ boundary interpolation
→ Monte Carlo error propagation
→ numerical geologic time scale
```

이 장의 가장 중요한 메시지는 다음이다.

> Stage와 biozone의 수치 연대는 직접 측정된 값이 아니라,  
> 여러 연대자료와 상대 층서척도, 오차모델과 smoothing 가정을 결합해 계산한 모델 결과다.

GTS2012의 개선은 spline 자체보다 경계연대의 불확실성을 Monte Carlo로 직접 모사했다는 점에 있다.

그러나 결과 신뢰구간은 smoothness, 독립오차와 초기 상대척도 같은 모델 가정을 포함하므로, 완전한 객관적 진실이라기보다 특정 입력과 통계절차에 의존하는 버전형 추정치다.

이 점에서 Chapter 14는 cdGTS의 핵심 철학과 매우 잘 맞는다. 방사성연대, 층서 위치, 상대척도, spline, outlier 처리, Monte Carlo replicate와 경계연대를 하나의 계산 그래프로 보존하면, 새로운 연대와 상관자료가 추가될 때 전체 시간척도를 자동으로 다시 계산할 수 있다.

---

## 출처

Agterberg, F.P., Hammer, O. & Gradstein, F.M. (2012). **Statistical Procedures**. In *The Geologic Time Scale 2012*, Chapter 14, pp. 269–273.
