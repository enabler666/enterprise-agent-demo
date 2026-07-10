package com.enabler.requirement.domain;

import java.time.OffsetDateTime;

public record RequirementQuery(
        String requirementNo,
        String title,
        String applicantId,
        String applicantName,
        String department,
        RequirementStatus status,
        OffsetDateTime createdFrom,
        OffsetDateTime createdTo,
        int page,
        int size) {
}
