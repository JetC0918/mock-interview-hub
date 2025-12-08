/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { User } from '../models/User';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AuthService {
    /**
     * Login user
     * @param requestBody
     * @returns User Successful login
     * @throws ApiError
     */
    public static postAuthLogin(
        requestBody: {
            email: string;
            password: string;
        },
    ): CancelablePromise<User> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/auth/login',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                401: `Invalid credentials`,
            },
        });
    }
    /**
     * Register new user
     * @param requestBody
     * @returns User User created
     * @throws ApiError
     */
    public static postAuthSignup(
        requestBody: {
            username: string;
            email: string;
            password: string;
        },
    ): CancelablePromise<User> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/auth/signup',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                400: `Invalid input`,
            },
        });
    }
    /**
     * Logout user
     * @returns any Successfully logged out
     * @throws ApiError
     */
    public static postAuthLogout(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/auth/logout',
        });
    }
    /**
     * Get current authenticated user
     * @returns User Current user
     * @throws ApiError
     */
    public static getAuthMe(): CancelablePromise<User> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/auth/me',
            errors: {
                401: `Not authenticated`,
            },
        });
    }
    /**
     * Join as guest
     * @param requestBody
     * @returns User Guest user created
     * @throws ApiError
     */
    public static postAuthGuest(
        requestBody: {
            username: string;
        },
    ): CancelablePromise<User> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/auth/guest',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
}
