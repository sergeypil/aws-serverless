package com.task05;


import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.syndicate.deployment.annotations.lambda.LambdaHandler;
import com.syndicate.deployment.model.RetentionSetting;
import com.task05.model.Event;

import com.task05.model.RequestBody;
import software.amazon.awssdk.enhanced.dynamodb.DynamoDbEnhancedClient;
import software.amazon.awssdk.enhanced.dynamodb.DynamoDbTable;
import software.amazon.awssdk.enhanced.dynamodb.TableSchema;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.Map;

@LambdaHandler(lambdaName = "api_handler",
			   roleName = "api_handler-role",
			   logsExpiration = RetentionSetting.SYNDICATE_ALIASES_SPECIFIED,
			   timeout = 60
)
public class ApiHandler implements RequestHandler<RequestBody, Map<String, Object>> {

	private final DynamoDbEnhancedClient enhancedClient = DynamoDbEnhancedClient.create();
	private static final String TABLE_NAME = "cmtr-d7361a80-Events-test";

	public Map<String, Object> handleRequest(RequestBody request, Context context) {
		int principalId = request.getPrincipalId();
		Map<String, String> content = request.getContent();
		
		String id = java.util.UUID.randomUUID().toString();
		String createdAt = LocalDateTime.now().format(DateTimeFormatter.ISO_DATE_TIME);
		Event event = new Event();
		event.setId(id);
		event.setBody(content);
		event.setCreatedAt(createdAt);
		event.setPrincipalId(principalId);

		DynamoDbTable<Event> table = enhancedClient.table(TABLE_NAME, TableSchema.fromBean(Event.class));
		table.putItem(event);

		Map<String, Object> responseBody = new HashMap<>();
		responseBody.put("statusCode", 201);
		responseBody.put("event", event);
		return responseBody;
	}
}