package com.task04;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.lambda.runtime.events.SNSEvent;
import com.amazonaws.services.lambda.runtime.events.SNSEvent.SNSRecord;
import com.syndicate.deployment.annotations.events.SnsEventSource;
import com.syndicate.deployment.annotations.lambda.LambdaHandler;
import com.syndicate.deployment.model.RetentionSetting;

import java.util.List;
import java.util.logging.Logger;

@LambdaHandler(lambdaName = "sns_handler",
			   roleName = "sns_handler-role",
			   logsExpiration = RetentionSetting.SYNDICATE_ALIASES_SPECIFIED
)
@SnsEventSource(targetTopic = "lambda_topic")
public class SnsHandler implements RequestHandler<SNSEvent, String> {
	private static final Logger log = Logger.getLogger(SnsHandler.class.getName());

	public String handleRequest(SNSEvent event, Context context) {
		log.info("SNSEvent: " + event);
		List<SNSRecord> records = event.getRecords();
		for (SNSRecord snsRecord  : records) {
			String message = snsRecord.getSNS().getMessage();
			log.info("Message: " + message);
		}
		return "Lambda is finished.";
	}
}