package com.enabler.requirement.api;

import com.enabler.requirement.domain.RequirementStatus;
import java.time.LocalDate;
import java.time.OffsetDateTime;

public record RequirementDto(
        Long id,
        String requirementNo,
        String title,
        String description,
        String applicantId,
        String applicantName,
        String department,
        String type,
        RequirementStatus status,
        String currentNode,
        LocalDate expectedCompletionDate,
        OffsetDateTime createdAt,
        OffsetDateTime updatedAt) {
}
