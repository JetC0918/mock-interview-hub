/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ChatMessage } from '../models/ChatMessage';
import type { ChatMessageCreate } from '../models/ChatMessageCreate';
import type { GuestSessionJoin } from '../models/GuestSessionJoin';
import type { GuestSessionJoinResponse } from '../models/GuestSessionJoinResponse';
import type { PublicChatMessage } from '../models/PublicChatMessage';
import type { PublicSession } from '../models/PublicSession';
import type { Session } from '../models/Session';
import type { SessionCodeUpdate } from '../models/SessionCodeUpdate';
import type { SessionCreate } from '../models/SessionCreate';
import type { SessionCursorUpdate } from '../models/SessionCursorUpdate';
import type { SessionJoin } from '../models/SessionJoin';
import type { SessionLanguageUpdate } from '../models/SessionLanguageUpdate';
import type { SessionRevisionResponse } from '../models/SessionRevisionResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class SessionsService {
    /** Legacy adapter aliases; new generated names remain the canonical API. */
    public static postSessions(requestBody: SessionCreate): CancelablePromise<Session> {
        return this.createSessionSessionsPost({ requestBody });
    }
    public static postSessionsJoin(id: string, requestBody: SessionJoin): CancelablePromise<Session> {
        return this.joinSessionSessionsIdJoinPost({ id, requestBody });
    }
    public static postSessionsJoinByPin(requestBody: SessionJoin): CancelablePromise<Session> {
        return this.joinByPinSessionsJoinByPinPost({ requestBody });
    }
    public static getSessions1(id: string): CancelablePromise<PublicSession> {
        return this.getSessionSessionsIdGet({ id });
    }
    public static getSessionsPrivate(id: string): CancelablePromise<Session> {
        return this.getPrivateSessionSessionsIdPrivateGet({ id });
    }
    public static putSessionsCode(id: string, requestBody: SessionCodeUpdate): CancelablePromise<SessionRevisionResponse> {
        return this.updateCodeSessionsIdCodePut({ id, requestBody });
    }
    public static putSessionsLanguage(id: string, requestBody: SessionLanguageUpdate): CancelablePromise<SessionRevisionResponse> {
        return this.updateLanguageSessionsIdLanguagePut({ id, requestBody });
    }
    public static putSessionsCursor(id: string, requestBody: SessionCursorUpdate): CancelablePromise<any> {
        return this.updateCursorSessionsIdCursorPut({ id, requestBody });
    }
    public static postSessionsLeave(id: string): CancelablePromise<any> {
        return this.leaveSessionSessionsIdLeavePost({ id });
    }
    public static postSessionsEnd(id: string): CancelablePromise<any> {
        return this.endSessionSessionsIdEndPost({ id });
    }
    public static postSessionsStart(id: string): CancelablePromise<any> {
        return this.startSessionSessionsIdStartPost({ id });
    }
    public static getSessions(): CancelablePromise<Array<Session>> {
        return this.getSessionsSessionsGet();
    }
    public static postSessionsMessages(id: string, requestBody: ChatMessageCreate): CancelablePromise<ChatMessage> {
        return this.sendMessageSessionsIdMessagesPost({ id, requestBody });
    }
    public static getSessionsMessages(id: string): CancelablePromise<Array<ChatMessage>> {
        return this.getMessagesSessionsIdMessagesGet({ id });
    }
    /**
     * Get Sessions
     * Get the current user's non-ended sessions (requires authentication).
     * @returns Session Successful Response
     * @throws ApiError
     */
    public static getSessionsSessionsGet(): CancelablePromise<Array<Session>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/sessions',
        });
    }
    /**
     * Create Session
     * Create a new session (requires authentication).
     * @returns Session Successful Response
     * @throws ApiError
     */
    public static createSessionSessionsPost({
        requestBody,
    }: {
        requestBody: SessionCreate,
    }): CancelablePromise<Session> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/sessions',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Join By Pin
     * Join a session by high-entropy secret (requires authentication).
     * @returns Session Successful Response
     * @throws ApiError
     */
    public static joinByPinSessionsJoinByPinPost({
        requestBody,
    }: {
        requestBody: SessionJoin,
    }): CancelablePromise<Session> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/sessions/join-by-pin',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Public Sessions
     * List bounded non-ended sessions for unauthenticated spectating.
     * @returns PublicSession Successful Response
     * @throws ApiError
     */
    public static getPublicSessionsSessionsPublicGet(): CancelablePromise<Array<PublicSession>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/sessions/public',
        });
    }
    /**
     * Get Session
     * Get the restricted public session projection for direct-link viewing.
     * @returns PublicSession Successful Response
     * @throws ApiError
     */
    public static getSessionSessionsIdGet({
        id,
    }: {
        id: string,
    }): CancelablePromise<PublicSession> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/sessions/{id}',
            path: {
                'id': id,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Code
     * Update session code (requires session participation).
     * @returns SessionRevisionResponse Successful Response
     * @throws ApiError
     */
    public static updateCodeSessionsIdCodePut({
        id,
        requestBody,
    }: {
        id: string,
        requestBody: SessionCodeUpdate,
    }): CancelablePromise<SessionRevisionResponse> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/sessions/{id}/code',
            path: {
                'id': id,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Cursor
     * Update cursor position (requires session participation).
     * @returns any Successful Response
     * @throws ApiError
     */
    public static updateCursorSessionsIdCursorPut({
        id,
        requestBody,
    }: {
        id: string,
        requestBody: SessionCursorUpdate,
    }): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/sessions/{id}/cursor',
            path: {
                'id': id,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * End Session
     * End a session (requires host role).
     * @returns any Successful Response
     * @throws ApiError
     */
    public static endSessionSessionsIdEndPost({
        id,
    }: {
        id: string,
    }): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/sessions/{id}/end',
            path: {
                'id': id,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Start Session
     * Start a waiting session exactly once as its host.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static startSessionSessionsIdStartPost({
        id,
    }: {
        id: string,
    }): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/sessions/{id}/start',
            path: {
                'id': id,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Guest Join Session
     * Validate admission before creating any durable guest/auth state.
     * @returns GuestSessionJoinResponse Successful Response
     * @throws ApiError
     */
    public static guestJoinSessionSessionsIdGuestJoinPost({
        id,
        requestBody,
    }: {
        id: string,
        requestBody: GuestSessionJoin,
    }): CancelablePromise<GuestSessionJoinResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/sessions/{id}/guest-join',
            path: {
                'id': id,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Join Session
     * Join a session with its high-entropy secret (requires authentication).
     * @returns Session Successful Response
     * @throws ApiError
     */
    public static joinSessionSessionsIdJoinPost({
        id,
        requestBody,
    }: {
        id: string,
        requestBody: SessionJoin,
    }): CancelablePromise<Session> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/sessions/{id}/join',
            path: {
                'id': id,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Rotate Join Secret
     * Rotate a host's bearer join secret, revoking the previous secret.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static rotateJoinSecretSessionsIdJoinSecretRotatePost({
        id,
    }: {
        id: string,
    }): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/sessions/{id}/join-secret/rotate',
            path: {
                'id': id,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Language
     * Update session language (requires session participation).
     * @returns SessionRevisionResponse Successful Response
     * @throws ApiError
     */
    public static updateLanguageSessionsIdLanguagePut({
        id,
        requestBody,
    }: {
        id: string,
        requestBody: SessionLanguageUpdate,
    }): CancelablePromise<SessionRevisionResponse> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/sessions/{id}/language',
            path: {
                'id': id,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Leave Session
     * Leave a session (requires authentication).
     * @returns any Successful Response
     * @throws ApiError
     */
    public static leaveSessionSessionsIdLeavePost({
        id,
    }: {
        id: string,
    }): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/sessions/{id}/leave',
            path: {
                'id': id,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Messages
     * Get chat messages (requires session participation).
     * @returns ChatMessage Successful Response
     * @throws ApiError
     */
    public static getMessagesSessionsIdMessagesGet({
        id,
    }: {
        id: string,
    }): CancelablePromise<Array<ChatMessage>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/sessions/{id}/messages',
            path: {
                'id': id,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Send Message
     * Send a chat message (requires session participation).
     * @returns ChatMessage Successful Response
     * @throws ApiError
     */
    public static sendMessageSessionsIdMessagesPost({
        id,
        requestBody,
    }: {
        id: string,
        requestBody: ChatMessageCreate,
    }): CancelablePromise<ChatMessage> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/sessions/{id}/messages',
            path: {
                'id': id,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Private Session
     * Get full session data for an authenticated participant.
     * @returns Session Successful Response
     * @throws ApiError
     */
    public static getPrivateSessionSessionsIdPrivateGet({
        id,
    }: {
        id: string,
    }): CancelablePromise<Session> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/sessions/{id}/private',
            path: {
                'id': id,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Public Messages
     * @returns PublicChatMessage Successful Response
     * @throws ApiError
     */
    public static getPublicMessagesSessionsIdPublicMessagesGet({
        id,
        limit = 50,
    }: {
        id: string,
        limit?: number,
    }): CancelablePromise<Array<PublicChatMessage>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/sessions/{id}/public-messages',
            path: {
                'id': id,
            },
            query: {
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
