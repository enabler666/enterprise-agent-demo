package com.enabler.requirement.repository;

import static org.assertj.core.api.Assertions.assertThat;

import com.enabler.requirement.domain.RequirementQuery;
import com.enabler.requirement.domain.RequirementStatus;
import java.time.OffsetDateTime;
import org.junit.jupiter.api.Test;

class InMemoryRequirementRepositoryTest {

    private final InMemoryRequirementRepository repository = new InMemoryRequirementRepository();

    @Test
    void filtersByPartialTitleAndStatus() {
        RequirementQuery query = query("服务器", RequirementStatus.EXECUTING, 0, 20);

        assertThat(repository.findAll(query))
                .extracting(requirement -> requirement.requirementNo())
                .containsExactly("XQ202607002");
        assertThat(repository.count(query)).isEqualTo(1);
    }

    @Test
    void filtersByInclusiveCreatedRangeAndPaginates() {
        RequirementQuery query = new RequirementQuery(
                null, null, null, null, null, null,
                OffsetDateTime.parse("2026-07-01T00:00:00+08:00"),
                OffsetDateTime.parse("2026-07-31T23:59:59+08:00"), 1, 3);

        assertThat(repository.count(query)).isEqualTo(7);
        assertThat(repository.findAll(query)).hasSize(3);
    }

    @Test
    void findsExactRequirementNumber() {
        assertThat(repository.findByRequirementNo("XQ202607001")).isPresent();
        assertThat(repository.findByRequirementNo("xq202607001")).isEmpty();
    }

    private RequirementQuery query(String title, RequirementStatus status, int page, int size) {
        return new RequirementQuery(
                null, title, null, null, null, status, null, null, page, size);
    }
}
