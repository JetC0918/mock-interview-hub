/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AIAssistRequest } from '../models/AIAssistRequest';
import type { AIAssistResponse } from '../models/AIAssistResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AiAssistantService {
    /**
     * Get Ai Assistance
     * Get AI-powered guidance for a coding question.
     * Requires authentication.
     * @returns AIAssistResponse Successful Response
     * @throws ApiError
     */
    public static getAiAssistanceAiAssistPost({
        requestBody,
    }: {
        requestBody: AIAssistRequest,
    }): CancelablePromise<AIAssistResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/ai/assist',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
