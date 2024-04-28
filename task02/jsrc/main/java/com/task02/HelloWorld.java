package com.task02;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.syndicate.deployment.annotations.lambda.LambdaHandler;
import com.syndicate.deployment.annotations.lambda.LambdaUrlConfig;
import com.syndicate.deployment.model.RetentionSetting;
import com.syndicate.deployment.model.lambda.url.AuthType;
import com.syndicate.deployment.model.lambda.url.InvokeMode;

import java.util.HashMap;
import java.util.Map;

@LambdaHandler(lambdaName = "hello_world",
	roleName = "hello_world-role",
	logsExpiration = RetentionSetting.SYNDICATE_ALIASES_SPECIFIED
)
@LambdaUrlConfig(
	authType = AuthType.NONE,
	invokeMode = InvokeMode.BUFFERED
)
public class HelloWorld implements RequestHandler<Object, Map<String, Object>> {

	ObjectMapper objectMapper = new ObjectMapper();

	@Override
	public Map<String, Object> handleRequest(Object request, Context context) {
		context.getLogger().log(request.toString());
		Map<String, Object> resultMap = new HashMap<>();
		Map<String, Object> bodyMap = new HashMap<>();
		if (request instanceof Map) {
			Map<String, Object> requestMap = (Map<String, Object>) request;
			Object rawPath = requestMap.get("rawPath");
			if ("/hello".equals(rawPath)) {
				context.getLogger().log("Hello from Lambda");
				bodyMap.put("statusCode", 200);
				bodyMap.put("message", "Hello from Lambda");
			} else {
				context.getLogger().log("Resource not found");
				bodyMap.put("statusCode", 404);
				bodyMap.put("message", "Resource not found");
			}
			resultMap.put("statusCode", 200);
			resultMap.put("body", bodyMap);
		}
		return resultMap;
	}
}     