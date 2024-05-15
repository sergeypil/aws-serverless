package com.task04;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.lambda.runtime.events.SQSEvent;
import com.amazonaws.services.lambda.runtime.events.SQSEvent.SQSMessage;
import com.syndicate.deployment.annotations.events.SqsTriggerEventSource;
import com.syndicate.deployment.annotations.lambda.LambdaHandler;
import com.syndicate.deployment.model.RetentionSetting;

import java.util.List;
import java.util.logging.Logger;

@LambdaHandler(lambdaName = "sqs_handler",
			   roleName = "sqs_handler-role",
			   isPublishVersion = true,
			   aliasName = "${lambdas_alias_name}",
			   logsExpiration = RetentionSetting.SYNDICATE_ALIASES_SPECIFIED
)
@SqsTriggerEventSource(targetQueue = "async_queue",
					   batchSize = 1)
public class SqsHandler implements RequestHandler<SQSEvent, String> {
	private static final Logger log = Logger.getLogger(SqsHandler.class.getName());
	
	public String handleRequest(SQSEvent event, Context context) {
		log.info("SQSEvent: " + event);
		List<SQSMessage> records = event.getRecords();
		for (SQSMessage sqsMessage  : records) {
			String message = sqsMessage .getBody();
			log.info("Message: " + message);
		}
		return "Lambda is finished.";
	}
}
