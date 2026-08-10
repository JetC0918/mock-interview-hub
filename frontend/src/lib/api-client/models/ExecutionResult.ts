/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { TestResult } from './TestResult';
export type ExecutionResult = {
    executionTime: number;
    exitCode: number;
    stderr: string;
    stdout: string;
    testResults?: (Array<TestResult> | null);
};

