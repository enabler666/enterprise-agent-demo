package com.enabler.requirement.repository;

import static org.assertj.core.api.Assertions.assertThat;

import com.enabler.requirement.domain.RequirementQuery;
import com.enabler.requirement.domain.RequirementStatus;
import java.time.OffsetDateTime;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.test.context.ActiveProfiles;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.mysql.MySQLContainer;

@SpringBootTest
@ActiveProfiles("mysql")
@Testcontainers(disabledWithoutDocker = true)
class MyBatisRequirementRepositoryIntegrationTest {

    @Container
    @ServiceConnection
    static final MySQLContainer MYSQL = new MySQLContainer("mysql:8.4")
            .withDatabaseName("enterprise_support")
            .withUsername("enterprise_support")
            .withPassword("integration-test-password");

    @Autowired
    private RequirementRepository repository;

    @Test
    void activatesMyBatisRepositoryAndLoadsFlywayData() {
        assertThat(repository).isInstanceOf(MyBatisRequirementRepository.class);
        assertThat(repository.count(emptyQuery())).isEqualTo(12);
        assertThat(repository.findByRequirementNo("XQ202607001"))
                .get()
                .extracting(value -> value.title(), value -> value.status())
                .containsExactly("新增生产服务器", RequirementStatus.PENDING_APPROVAL);
    }

    @Test
    void appliesDatabaseFiltersAndPaginationWithInMemorySemantics() {
        RequirementQuery query = new RequirementQuery(
                null, "服务器", null, null, null, RequirementStatus.EXECUTING,
                OffsetDateTime.parse("2026-07-01T00:00:00+08:00"),
                OffsetDateTime.parse("2026-07-31T23:59:59+08:00"), 0, 1);

        assertThat(repository.count(query)).isEqualTo(1);
        assertThat(repository.findAll(query))
                .extracting(value -> value.requirementNo())
                .containsExactly("XQ202607002");
    }

    private RequirementQuery emptyQuery() {
        return new RequirementQuery(
                null, null, null, null, null, null, null, null, 0, 20);
    }
}
