package com.enabler.requirement.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.enabler.requirement.api.RequirementQueryRequest;
import com.enabler.requirement.domain.RequirementStatus;
import com.enabler.requirement.exception.RequirementNotFoundException;
import com.enabler.requirement.repository.InMemoryRequirementRepository;
import java.time.OffsetDateTime;
import org.junit.jupiter.api.Test;

class RequirementServiceTest {

    private final RequirementService service =
            new RequirementService(new InMemoryRequirementRepository());

    @Test
    void returnsRequirementDto() {
        assertThat(service.getByRequirementNo("XQ202607001").title())
                .isEqualTo("新增生产服务器");
    }

    @Test
    void returnsProgressDto() {
        assertThat(service.getProgress("XQ202607002"))
                .extracting(progress -> progress.status(), progress -> progress.currentNode())
                .containsExactly(RequirementStatus.EXECUTING, "执行中");
    }

    @Test
    void rejectsUnknownRequirement() {
        assertThatThrownBy(() -> service.getByRequirementNo("XQ-NOT-FOUND"))
                .isInstanceOf(RequirementNotFoundException.class)
                .hasMessage("未找到需求 XQ-NOT-FOUND");
    }

    @Test
    void rejectsReversedCreatedRange() {
        RequirementQueryRequest request = new RequirementQueryRequest(
                null, null, null, null, null, null,
                OffsetDateTime.parse("2026-07-02T00:00:00+08:00"),
                OffsetDateTime.parse("2026-07-01T00:00:00+08:00"), 0, 20);

        assertThatThrownBy(() -> service.search(request))
                .isInstanceOf(IllegalArgumentException.class);
    }
}
