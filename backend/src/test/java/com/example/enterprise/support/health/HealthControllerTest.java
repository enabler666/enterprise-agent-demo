package com.example.enterprise.support.health;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

class HealthControllerTest {

    @Test
    void returnsUpStatus() {
        assertThat(new HealthController().health()).containsEntry("status", "UP");
    }
}
