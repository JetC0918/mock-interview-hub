/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type PublicChatMessage = {
    authorType: PublicChatMessage.authorType;
    message: string;
    timestamp: string;
    username: string;
};
export namespace PublicChatMessage {
    export enum authorType {
        USER = 'user',
        ASSISTANT = 'assistant',
    }
}

