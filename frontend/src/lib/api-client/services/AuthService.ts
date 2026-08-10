/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { User } from '../models/User';
import type { UserCreate } from '../models/UserCreate';
import type { UserLogin } from '../models/UserLogin';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AuthService {
    /** Backwards-compatible aliases retained for existing frontend adapters. */
    public static postAuthLogin(requestBody: import('../models/UserLogin').UserLogin): CancelablePromise<import('../models/User').User> {
        return this.loginAuthLoginPost({ requestBody });
    }
    public static postAuthSignup(requestBody: import('../models/UserCreate').UserCreate): CancelablePromise<import('../models/User').User> {
        return this.signupAuthSignupPost({ requestBody });
    }
    public static postAuthLogout(): CancelablePromise<any> {
        return this.logoutAuthLogoutPost({ sessionToken: undefined });
    }
    public static getAuthMe(): CancelablePromise<import('../models/User').User> {
        return this.getCurrentUserAuthMeGet();
    }
    public static postAuthGuest(requestBody: { username: string }): CancelablePromise<import('../models/User').User> {
        void requestBody;
        throw new Error('Standalone guest identity creation is disabled; use session guest admission.');
    }
    /**
     * Login
     * Login with email and password.
     * @returns User Successful Response
     * @throws ApiError
     */
    public static loginAuthLoginPost({
        requestBody,
    }: {
        requestBody: UserLogin,
    }): CancelablePromise<User> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/auth/login',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Logout
     * Revoke and clear the current session cookie.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static logoutAuthLogoutPost({
        sessionToken,
    }: {
        sessionToken?: (string | null),
    }): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/auth/logout',
            cookies: {
                'session_token': sessionToken,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Current User
     * Get the current authenticated user.
     * @returns User Successful Response
     * @throws ApiError
     */
    public static getCurrentUserAuthMeGet(): CancelablePromise<User> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/auth/me',
        });
    }
    /**
     * Signup
     * Create a new account.
     * @returns User Successful Response
     * @throws ApiError
     */
    public static signupAuthSignupPost({
        requestBody,
    }: {
        requestBody: UserCreate,
    }): CancelablePromise<User> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/auth/signup',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
