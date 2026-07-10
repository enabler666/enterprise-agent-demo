package com.enabler.requirement.domain;

import java.time.LocalDate;
import java.time.OffsetDateTime;

public record Requirement(
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
