package medviet.data_access

import future.keywords.if
import future.keywords.in

default allow := false

allow if {
    permitted
    not deny
}

permitted if {
    input.user.role == "admin"
}

permitted if {
    input.user.role == "ml_engineer"
    input.resource in {"training_data", "model_artifacts", "aggregated_metrics"}
    input.action in {"read", "write"}
}

permitted if {
    input.user.role == "data_analyst"
    input.resource == "aggregated_metrics"
    input.action == "read"
}

permitted if {
    input.user.role == "data_analyst"
    input.resource == "reports"
    input.action == "write"
}

permitted if {
    input.user.role == "intern"
    input.resource == "sandbox_data"
    input.action in {"read", "write"}
}

deny if {
    input.user.role == "ml_engineer"
    input.resource == "production_data"
    input.action == "delete"
}

deny if {
    input.data_classification == "restricted"
    input.destination_country != "VN"
}
