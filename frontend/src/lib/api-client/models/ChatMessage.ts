/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type ChatMessage = {
    authorType: ChatMessage.authorType;
    id: string;
    message: string;
    participantId: string;
    timestamp: string;
    username: string;
};
export namespace ChatMessage {
    export enum authorType {
        USER = 'user',
        ASSISTANT = 'assistant',
    }
}

