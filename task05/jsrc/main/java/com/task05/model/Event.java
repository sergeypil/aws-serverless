    package com.task05.model;
    
    import software.amazon.awssdk.enhanced.dynamodb.mapper.annotations.DynamoDbBean;
    import software.amazon.awssdk.enhanced.dynamodb.mapper.annotations.DynamoDbPartitionKey;

    import java.util.Map;
    
    
    @DynamoDbBean
    public class Event {
        private String id;
        private int principalId;
        private String createdAt;
        private Map<String, String> body;

        @DynamoDbPartitionKey
        public String getId() {
            return id;
        }

        public void setId(String id) {
            this.id = id;
        }

        public int getPrincipalId() {
            return principalId;
        }

        public void setPrincipalId(int principalId) {
            this.principalId = principalId;
        }

        public String getCreatedAt() {
            return createdAt;
        }

        public void setCreatedAt(String createdAt) {
            this.createdAt = createdAt;
        }

        public Map<String, String> getBody() {
            return body;
        }

        public void setBody(Map<String, String> body) {
            this.body = body;
        }
    }