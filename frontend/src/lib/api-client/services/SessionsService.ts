/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CursorPosition } from '../models/CursorPosition';
import type { Session } from '../models/Session';
import type { SupportedLanguage } from '../models/SupportedLanguage';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class SessionsService {
    /**
     * Get active sessions
     * @returns Session List of active sessions
     * @throws ApiError
     */
    public static getSessions(): CancelablePromise<Array<Session>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/sessions',
        });
    }
    /**
     * Get non-ended sessions for unauthenticated spectating
     * @returns Session List of public sessions
     * @throws ApiError
     */
    public static getSessionsPublic(): CancelablePromise<Array<Session>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/sessions/public',
        });
    }
    /**
     * Create a new session
     * @param requestBody
     * @returns Session Session created
     * @throws ApiError
     */
    public static postSessions(
        requestBody: {
            title: string;
            language?: SupportedLanguage;
        },
    ): CancelablePromise<Session> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/sessions',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Get session by ID
     * @param id
     * @returns Session Session details
     * @throws ApiError
     */
    public static getSessions1(
        id: string,
    ): CancelablePromise<Session> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/sessions/{id}',
            path: {
                'id': id,
            },
            errors: {
                404: `Session not found`,
            },
        });
    }
    /**
     * Get full session details for an authenticated participant
     * @param id
     * @returns Session Full session details
     * @throws ApiError
     */
    public static getSessionsPrivate(
        id: string,
    ): CancelablePromise<Session> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/sessions/{id}/private',
            path: {
                'id': id,
            },
            errors: {
                403: `Not a participant`,
                404: `Session not found`,
            },
        });
    }
    /**
     * Join a session using ID and PIN
     * @param id
     * @param requestBody
     * @returns Session Successfully joined
     * @throws ApiError
     */
    public static postSessionsJoin(
        id: string,
        requestBody: {
            pin: string;
        },
    ): CancelablePromise<Session> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/sessions/{id}/join',
            path: {
                'id': id,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                403: `Invalid PIN`,
            },
        });
    }
    /**
     * Join a session using only PIN
     * @param requestBody
     * @returns Session Successfully joined
     * @throws ApiError
     */
    public static postSessionsJoinByPin(
        requestBody: {
            pin: string;
        },
    ): CancelablePromise<Session> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/sessions/join-by-pin',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                404: `Session not found`,
            },
        });
    }
    /**
     * Update session code
     * @param id
     * @param requestBody
     * @returns any Code updated
     * @throws ApiError
     */
    public static putSessionsCode(
        id: string,
        requestBody: {
            code: string;
        },
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/sessions/{id}/code',
            path: {
                'id': id,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Update session language
     * @param id
     * @param requestBody
     * @returns any Language updated
     * @throws ApiError
     */
    public static putSessionsLanguage(
        id: string,
        requestBody: {
            language: SupportedLanguage;
        },
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/sessions/{id}/language',
            path: {
                'id': id,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Update user cursor position
     * @param id
     * @param requestBody
     * @returns any Cursor updated
     * @throws ApiError
     */
    public static putSessionsCursor(
        id: string,
        requestBody: {
            position: CursorPosition;
        },
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/sessions/{id}/cursor',
            path: {
                'id': id,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Leave a session
     * @param id
     * @returns any Left session
     * @throws ApiError
     */
    public static postSessionsLeave(
        id: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/sessions/{id}/leave',
            path: {
                'id': id,
            },
        });
    }
    /**
     * End a session (Host only)
     * @param id
     * @returns any Session ended
     * @throws ApiError
     */
    public static postSessionsEnd(
        id: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/sessions/{id}/end',
            path: {
                'id': id,
            },
        });
    }
}
