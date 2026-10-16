# Spring Boot Patterns

Non-default Spring Boot practices. Layering, repositories, DTOs, caching, async and filters follow standard Spring; this file carries only the gotchas.

## Error Responses

Pick one mechanism per service: `spring.mvc.problemdetails.enabled=true` (RFC 7807, Spring Boot 3+) or a custom `@RestControllerAdvice` with an `ApiError` type. A catch-all `Exception` handler logs the stack trace and returns a generic message.

## Rate Limiting (Filter + Bucket4j)

Identify clients with `request.getRemoteAddr()`. Never read `X-Forwarded-For` directly: clients spoof it. Behind a reverse proxy:

1. Set `server.forward-headers-strategy=NATIVE` or `FRAMEWORK` (register `ForwardedHeaderFilter` for `FRAMEWORK`)
2. Configure the proxy to overwrite `X-Forwarded-For`, not append
3. Configure `server.tomcat.remoteip.trusted-proxies` (or the container equivalent)

```java
@Component
public class RateLimitFilter extends OncePerRequestFilter {
  // ceiling: unbounded per-IP map, in-memory per instance;
  // upgrade: Caffeine with expireAfterAccess, or Redis-backed Bucket4j
  private final Map<String, Bucket> buckets = new ConcurrentHashMap<>();

  @Override
  protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
      FilterChain filterChain) throws ServletException, IOException {
    Bucket bucket = buckets.computeIfAbsent(request.getRemoteAddr(),
        k -> Bucket.builder()
            .addLimit(Bandwidth.builder().capacity(100).refillGreedy(100, Duration.ofMinutes(1)).build())
            .build());

    if (bucket.tryConsume(1)) {
      filterChain.doFilter(request, response);
    } else {
      response.setStatus(HttpStatus.TOO_MANY_REQUESTS.value());
    }
  }
}
```

`Bandwidth.classic` and `Refill.greedy` are deprecated in current Bucket4j (see `Bandwidth.builder()`).

## Production Defaults

- `@Transactional(readOnly = true)` for queries
- Size HikariCP pools for the workload and set timeouts
- Keep background jobs idempotent and observable
- Observability: structured JSON logs (Logback encoder), Micrometer metrics, Micrometer Tracing (OpenTelemetry or Brave)
