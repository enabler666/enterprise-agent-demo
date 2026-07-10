package com.enabler;

import static org.assertj.core.api.Assertions.assertThat;

import com.enabler.requirement.repository.InMemoryRequirementRepository;
import com.enabler.requirement.repository.RequirementRepository;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class EnterpriseSupportApplicationTest {

    @Autowired
    private RequirementRepository repository;

    @Test
    void startsWithInMemoryRepositoryByDefault() {
        assertThat(repository).isInstanceOf(InMemoryRequirementRepository.class);
        assertThat(repository.findByRequirementNo("XQ202607001")).isPresent();
    }
}
