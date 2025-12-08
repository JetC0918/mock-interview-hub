/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ChatMessage } from '../models/ChatMessage';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ChatService {
    /**
     * Get chat messages
     * @param id
     * @returns ChatMessage List of messages
     * @throws ApiError
     */
    public static getSessionsMessages(
        id: string,
    ): CancelablePromise<Array<ChatMessage>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/sessions/{id}/messages',
            path: {
                'id': id,
            },
        });
    }
    /**
     * Send a chat message
     * @param id
     * @param requestBody
     * @returns ChatMessage Message sent
     * @throws ApiError
     */
    public static postSessionsMessages(
        id: string,
        requestBody: {
            message: string;
        },
    ): CancelablePromise<ChatMessage> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/sessions/{id}/messages',
            path: {
                'id': id,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
}
