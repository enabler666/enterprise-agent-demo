package com.enabler.requirement.api;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.enabler.common.exception.GlobalExceptionHandler;
import com.enabler.common.trace.TraceIdFilter;
import com.enabler.requirement.repository.InMemoryRequirementRepository;
import com.enabler.requirement.service.RequirementService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

class RequirementControllerTest {

    private MockMvc mockMvc;

    @BeforeEach
    void setUp() {
        RequirementService service = new RequirementService(new InMemoryRequirementRepository());
        mockMvc = MockMvcBuilders.standaloneSetup(new RequirementController(service))
                .setControllerAdvice(new GlobalExceptionHandler())
                .addFilters(new TraceIdFilter())
                .build();
    }

    @Test
    void getsRequirementByNumberAndPropagatesTraceId() throws Exception {
        mockMvc.perform(get("/api/requirements/XQ202607001")
                        .header(TraceIdFilter.HEADER_NAME, "trace-test-001"))
                .andExpect(status().isOk())
                .andExpect(header().string(TraceIdFilter.HEADER_NAME, "trace-test-001"))
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.code").value("OK"))
                .andExpect(jsonPath("$.data.requirementNo").value("XQ202607001"))
                .andExpect(jsonPath("$.traceId").value("trace-test-001"));
    }

    @Test
    void searchesWithCombinedConditionsAndPagination() throws Exception {
        mockMvc.perform(get("/api/requirements")
                        .param("title", "服务器")
                        .param("status", "EXECUTING")
                        .param("page", "0")
                        .param("size", "1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.total").value(1))
                .andExpect(jsonPath("$.data.items[0].requirementNo").value("XQ202607002"))
                .andExpect(jsonPath("$.data.totalPages").value(1));
    }

    @Test
    void getsRequirementProgress() throws Exception {
        mockMvc.perform(get("/api/requirements/XQ202607002/progress"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.status").value("EXECUTING"))
                .andExpect(jsonPath("$.data.currentNode").value("执行中"));
    }

    @Test
    void returnsBusinessErrorWhenRequirementDoesNotExist() throws Exception {
        mockMvc.perform(get("/api/requirements/XQ-NOT-FOUND"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.code").value("REQUIREMENT_NOT_FOUND"))
                .andExpect(jsonPath("$.message").value("未找到需求 XQ-NOT-FOUND"))
                .andExpect(jsonPath("$.data").doesNotExist());
    }

    @Test
    void rejectsInvalidPageSize() throws Exception {
        mockMvc.perform(get("/api/requirements").param("size", "101"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value("INVALID_ARGUMENT"));
    }

    @Test
    void rejectsInvalidStatus() throws Exception {
        mockMvc.perform(get("/api/requirements").param("status", "UNKNOWN"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value("INVALID_ARGUMENT"));
    }
}
