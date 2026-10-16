# Java Coding Standards

Java 17+ conventions for Spring Boot and Quarkus. Tags: `[SPRING]` and `[QUARKUS]` mark framework-specific rules; untagged rules apply to both. Package layout follows the project (feature/domain first); only the Quarkus naming rule below is fixed.

## Core Principles

- Fail fast with meaningful exceptions
- Immutable by default; minimize shared mutable state
- **[QUARKUS]** Favor build-time over runtime processing; avoid runtime reflection

## Naming

```java
// [QUARKUS] JAX-RS classes end in *Resource
public class MarketResource {}

// [SPRING] REST classes end in *Controller
public class MarketController {}
```

## Immutability

Use records and final fields. Exception:

```java
// [QUARKUS] Panache active-record entities use public fields; Panache generates accessors at build time
@Entity
public class Market extends PanacheEntity {
  public String name;
  public MarketStatus status;
}
```

## Dependency Injection

```java
// [SPRING] Constructor injection; no @Autowired fields

// [QUARKUS] Constructor injection, or package-private @Inject field (avoids proxy issues)
@ApplicationScoped
public class MarketService {
  @Inject
  MarketRepository marketRepository;
}
```

- **[QUARKUS]** Default to `@ApplicationScoped` (client proxy, lazy instantiation). `@Singleton` is a pseudo-scope: no client proxy, created on injection; interceptors still work. Choose it only when eager creation is wanted.

## Reactive Patterns [QUARKUS]

```java
// Compose Uni/Multi; return them from endpoints
public Uni<OrderConfirmation> placeOrder(OrderRequest req) {
  return validateOrder(req)
      .chain(valid -> persistOrder(valid))
      .chain(order -> notifyFulfillment(order));
}

// FAIL: blocking call inside a Uni pipeline blocks the event loop
Market m = Market.find("slug", slug).firstResult();
return Uni.createFrom().item(m);

// FAIL: second subscribe to a shared Uni re-runs the source; use Uni.memoize()
shared.subscribe().with(m -> log(m));
shared.subscribe().with(m -> cache(m));
```

## Exceptions

- Unchecked domain exceptions (e.g. `MarketNotFoundException`); wrap technical exceptions with context
- Map exceptions to HTTP responses in one place:

```java
// [SPRING]
@RestControllerAdvice
public class GlobalExceptionHandler {
  @ExceptionHandler(MarketNotFoundException.class)
  public ResponseEntity<ErrorResponse> handle(MarketNotFoundException ex) {
    return ResponseEntity.status(404).body(ErrorResponse.from(ex));
  }
}

// [QUARKUS] Quarkus REST (formerly RESTEasy Reactive)
@ServerExceptionMapper
public RestResponse<ErrorResponse> handle(MarketNotFoundException ex) {
  return RestResponse.status(Status.NOT_FOUND, ErrorResponse.from(ex));
}
// [QUARKUS] classic RESTEasy: @Provider class implementing ExceptionMapper<T>
```

## Logging

Log key=value events with the framework logger:

```java
// [SPRING] SLF4J
log.info("fetch_market slug={}", slug);
log.error("failed_fetch_market slug={}", slug, ex);

// [QUARKUS] JBoss Logging; @Inject Logger log is also available
log.infof("fetch_market slug=%s", slug);
log.errorf(ex, "failed_fetch_market slug=%s", slug);
```

## Validation

**[QUARKUS]** Put `@Valid` on `@BeanParam`, `@RestForm`, and request body parameters.

## Configuration

```java
// [SPRING]
@ConfigurationProperties(prefix = "market")
public record MarketProperties(int maxPageSize, Duration cacheTtl) {}

// [QUARKUS] type-safe, validated at build/startup
@ConfigMapping(prefix = "market")
public interface MarketConfig {
  int maxPageSize();
  Duration cacheTtl();
}
```

## Testing Expectations

Test-first workflow and Spring examples: `tdd.md`. Framework-specific rules:

- **[SPRING]** `@WebMvcTest` for controller slices, `@DataJpaTest` for repository slices, `@SpringBootTest` for full integration. Replace beans with `@MockitoBean` (see `tdd.md`).
- **[QUARKUS]** Plain JUnit 5 + Mockito for unit tests (no `@QuarkusTest`). `@QuarkusTest` for CDI integration tests, `@InjectMock` to replace beans. Use Dev Services for database/Kafka/Redis instead of manual Testcontainers. `@QuarkusTestResource` manages custom external services.

## Code Smells [QUARKUS]

- Mixed `quarkus-rest` (or the older `quarkus-resteasy-reactive`) and classic `quarkus-resteasy` in one app: pick one stack
- Panache active-record and repository pattern in the same bounded context: pick one
