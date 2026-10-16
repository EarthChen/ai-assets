# Spring Boot TDD Workflow

Spring-specific test application. Cross-stack testing principles (boundaries, sociable/solitary, narrow integration, isolation rules, F.I.R.S.T): Read `../../testing-principles/SKILL.md`.

## Workflow

Red-green-refactor loop: the `tdd` skill. Coverage target: the global 80% testing rule, enforced by the JaCoCo `check` execution below.

## Slice Selection

| Layer | Annotation | Mocking |
| --- | --- | --- |
| Service | `@ExtendWith(MockitoExtension.class)` | `@Mock` + `@InjectMocks`; mock slow or side-effectful collaborators only |
| Controller | `@WebMvcTest(X.class)` + `MockMvc` | `@MockitoBean` for the service |
| Repository | `@DataJpaTest` + `@AutoConfigureTestDatabase(replace = NONE)` | none; real database via Testcontainers |
| Full flow | `@SpringBootTest` + `@AutoConfigureMockMvc` + `@ActiveProfiles("test")` | external boundaries only (third-party HTTP, brokers) |

- `@MockBean` is deprecated since Spring Boot 3.4 and removed in 4.0. Use `@MockitoBean` (`org.springframework.test.context.bean.override.mockito`).
- `@DataJpaTest` rolls back each test. For `@SpringBootTest`, `@Transactional` on the test class rolls back; tests that commit through other threads clean up in `@AfterEach`.

```java
@WebMvcTest(MarketController.class)
class MarketControllerTest {
  @Autowired MockMvc mockMvc;
  @MockitoBean MarketService marketService;

  @Test
  void returnsMarkets() throws Exception {
    when(marketService.list(any())).thenReturn(Page.empty());

    mockMvc.perform(get("/api/markets"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.content").isArray());
  }
}
```

## Testcontainers

- Use a real Postgres/Redis, not H2: dialect and behavior differ from production.
- Declare the container as a `static` field annotated `@Container @ServiceConnection` (Spring Boot 3.1+, needs `spring-boot-testcontainers`); Boot derives the datasource properties. Use `@DynamicPropertySource` only for services `@ServiceConnection` does not cover.
- The container class import path depends on the Testcontainers major version (2.x moved classes to `org.testcontainers.<module>`); copy it from the project's existing tests.

## Coverage (JaCoCo)

```xml
<plugin>
  <groupId>org.jacoco</groupId>
  <artifactId>jacoco-maven-plugin</artifactId>
  <version>0.8.14</version>
  <executions>
    <execution>
      <goals><goal>prepare-agent</goal></goals>
    </execution>
    <execution>
      <id>report</id>
      <phase>verify</phase>
      <goals><goal>report</goal></goals>
    </execution>
    <execution>
      <id>check</id>
      <phase>verify</phase>
      <goals><goal>check</goal></goals>
      <configuration>
        <rules>
          <rule>
            <element>BUNDLE</element>
            <limits>
              <limit>
                <counter>LINE</counter>
                <value>COVEREDRATIO</value>
                <minimum>0.80</minimum>
              </limit>
            </limits>
          </rule>
        </rules>
      </configuration>
    </execution>
  </executions>
</plugin>
```
