package com.enabler.requirement.repository;

import com.enabler.requirement.domain.Requirement;
import com.enabler.requirement.domain.RequirementQuery;
import java.util.List;
import java.util.Optional;

public interface RequirementRepository {

    Optional<Requirement> findByRequirementNo(String requirementNo);

    List<Requirement> findAll(RequirementQuery query);

    long count(RequirementQuery query);
}
