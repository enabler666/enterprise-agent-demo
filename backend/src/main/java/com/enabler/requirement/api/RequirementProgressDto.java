package com.enabler.requirement.api;

import com.enabler.requirement.domain.RequirementStatus;
import java.time.LocalDate;
import java.time.OffsetDateTime;

public record RequirementProgressDto(
        String requirementNo,
        String title,
        RequirementStatus status,
        String currentNode,
        OffsetDateTime createdAt,
        OffsetDateTime updatedAt,
        LocalDate expectedCompletionDate) {
}
