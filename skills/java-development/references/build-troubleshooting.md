# Build Troubleshooting

Reference for resolving Java build, compilation, and dependency errors. Consumed by the `java-development` skill (branch: build failing) and dispatched agents (`java-build-resolver`).

## Fix Patterns — General Java

| Error | Cause | Fix |
| ------- | ------- | ----- |
| `Annotation processor threw uncaught exception` | Lombok/MapStruct misconfiguration | Lombok/MapStruct must be declared under `annotationProcessorPaths` (Maven) or `annotationProcessor` (Gradle) — a plain `dependencies` entry is not enough |
| `Could not resolve: group:artifact:version` | Missing repository or wrong version | Add repository or fix version in POM |
| `artifacts could not be resolved` | Private repo or network issue | Check repository credentials / `settings.xml` |
| `Source option X is no longer supported` | Java version mismatch | Update `maven.compiler.source` / `targetCompatibility` |

## Fix Patterns — [SPRING] Spring Boot

| Error | Cause | Fix |
| ------- | ------- | ----- |
| `No qualifying bean of type X` | Missing `@Component`/`@Service` or component scan | Add annotation or fix scan base package |
| `Circular dependency involving X` | Constructor injection cycle | Refactor to break cycle or `@Lazy` on one leg |
| `BeanCreationException` | Missing config, bad property, or missing dependency | Check `application.yml`, dependency tree |
| `HttpMessageNotReadableException` | Malformed JSON or missing Jackson | Check `spring-boot-starter-web` includes Jackson |
| `Could not autowire. No beans of type found` | Missing bean or wrong profile | Check `@Profile`, `@ConditionalOn*`, component scan |
| `Failed to configure a DataSource` | Missing DB driver or datasource properties | Add driver dependency or `spring.datasource.*` config |
| `spring-boot-starter-* not found` | BOM version mismatch | Check `spring-boot-dependencies` BOM version in parent |

## Fix Patterns — [QUARKUS] Quarkus

| Error | Cause | Fix |
| ------- | ------- | ----- |
| `UnsatisfiedResolutionException` | Missing `@ApplicationScoped`/`@Inject` or extension | Add CDI annotation or `quarkus-*` extension |
| `AmbiguousResolutionException` | Multiple beans match injection point | Add `@Priority`, `@Alternative`, or qualifier |
| `Build step X threw an exception` | Build-time augmentation failure | Read full stack trace — usually missing extension, bad config, or reflection issue |
| `non-proxyable bean type` | Normal-scoped bean (e.g. `@ApplicationScoped`) is `final` or lacks a no-args constructor, and ArC cannot transform it | Remove `final`, add a no-args constructor, or use `@Singleton` (pseudo-scope, no proxy) |
| `ClassNotFoundException at native image build` | Missing reflection config | Add `@RegisterForReflection` or `reflect-config.json` entry |
| `BlockingNotAllowedOnIOThread` | Blocking call on Vert.x event loop | Add `@Blocking` to endpoint or use reactive client |
| `ConfigurationException: SRCFG*` | Missing/malformed config property | Check `application.properties` for required `quarkus.*` / `mp.*` keys |
| `quarkus-extension-* not found` | Wrong BOM version or extension not in BOM | Check `quarkus-bom` version; prefer `quarkus ext add` over hand-editing the POM |
| Dev mode hot reload failure | Incompatible change during dev mode | `./mvnw clean quarkus:dev` (or Gradle equivalent) |
| `Panache entity not enhanced` | Entity not detected at build time | Entity must be in a scanned package; check the panache extension is present |
| `RESTEASY* deployment failure` | Duplicate JAX-RS paths or mixed stacks | Check `@Path` uniqueness; do not mix `quarkus-rest` (formerly `quarkus-resteasy-reactive`) with classic `quarkus-resteasy` |

## Diagnostic Commands — gotchas only

Beyond the obvious (`compile`, `test`, `--version`), these carry non-discoverable knowledge:

```bash
# Dependency conflicts: -Dverbose shows who pulled the winning/losing version
./mvnw dependency:tree -Dverbose
./gradlew dependencyInsight --dependency <name> --configuration runtimeClasspath

# Effective POM: resolved inheritance/BOM — the truth when versions look right but aren't
./mvnw help:effective-pom

# Annotation processor debugging (Lombok/MapStruct silent failures)
./mvnw compile -X 2>&1 | grep -i "processor\|lombok\|mapstruct"

# Quarkus augmentation failures
./mvnw compile -X 2>&1 | grep -i "augment\|build step\|extension"
```

## Principles

- Fix root cause; ask the user before suppressing with `@SuppressWarnings`
- **[QUARKUS]**: check whether `@RegisterForReflection` is needed before writing reflection config manually
