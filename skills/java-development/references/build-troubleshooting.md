# Build Troubleshooting

Reference for resolving Java build, compilation, and dependency errors. Consumed by the `java-development` skill (branch: build failing) and dispatched agents (`java-build-resolver`).

## Fix Patterns — General Java

| Error | Cause | Fix |
| ------- | ------- | ----- |
| `cannot find symbol` | Missing import, typo, missing dependency | Add import or dependency |
| `incompatible types: X cannot be converted to Y` | Wrong type, missing cast | Add explicit cast or fix type |
| `method X in class Y cannot be applied to given types` | Wrong argument types or count | Fix arguments or check overloads |
| `variable X might not have been initialized` | Uninitialized local variable | Initialise before use |
| `non-static method X cannot be referenced from a static context` | Instance method called statically | Create instance or make method static |
| `reached end of file while parsing` | Missing closing brace | Add missing `}` |
| `package X does not exist` | Missing dependency or wrong import | Add dependency to `pom.xml`/`build.gradle` |
| `cannot access X, class file not found` | Missing transitive dependency | Add explicit dependency |
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
| `non-proxyable bean type` | `@Singleton` with interceptor or `final` class | Switch to `@ApplicationScoped` or remove `final` |
| `ClassNotFoundException at native image build` | Missing reflection config | Add `@RegisterForReflection` or `reflect-config.json` entry |
| `BlockingNotAllowedOnIOThread` | Blocking call on Vert.x event loop | Add `@Blocking` to endpoint or use reactive client |
| `ConfigurationException: SRCFG*` | Missing/malformed config property | Check `application.properties` for required `quarkus.*` / `mp.*` keys |
| `quarkus-extension-* not found` | Wrong BOM version or extension not in BOM | Check `quarkus-bom` version; prefer `quarkus ext add` over hand-editing the POM |
| Dev mode hot reload failure | Incompatible change during dev mode | `./mvnw clean quarkus:dev` (or Gradle equivalent) |
| `Panache entity not enhanced` | Entity not detected at build time | Entity must be in a scanned package; check the panache extension is present |
| `RESTEASY* deployment failure` | Duplicate JAX-RS paths or mixed stacks | Check `@Path` uniqueness; do not mix `quarkus-resteasy-reactive` with `quarkus-resteasy` |

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

# Native build prerequisite check
./mvnw package -Pnative -DskipTests 2>&1 | head -50

# Isolate compile errors from test failures
./mvnw compile -DskipTests
```

## Principles

- Surgical fixes only — fix the error, no refactoring
- Fix root cause over suppressing symptoms; `@SuppressWarnings` only with explicit approval
- Prefer adding missing imports over changing logic
- Re-run the build after each fix to verify
- **[QUARKUS]**: prefer `quarkus ext add` over hand-editing `pom.xml`; check whether `@RegisterForReflection` is needed before writing reflection config manually
