/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { TestResult } from './TestResult';
export type ExecutionResult = {
    stdout?: string;
    stderr?: string;
    exitCode?: number;
    executionTime?: number;
    testResults?: Array<TestResult>;
};

