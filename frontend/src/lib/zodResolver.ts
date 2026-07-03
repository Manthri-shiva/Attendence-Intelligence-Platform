import * as z from 'zod';

/**
 * Custom lightweight Zod resolver for React Hook Form.
 * Avoids extra third-party package dependencies while providing fully schema-backed Zod validation.
 */
export const zodResolver = <T extends z.ZodType<any, any>>(schema: T) => async (values: any) => {
  try {
    const data = schema.parse(values);
    return {
      values: data,
      errors: {},
    };
  } catch (error: any) {
    if (error instanceof z.ZodError) {
      const errors = error.errors.reduce((allErrors: any, currentError) => {
        const path = currentError.path[0] as string;
        return {
          ...allErrors,
          [path]: {
            type: currentError.code,
            message: currentError.message,
          },
        };
      }, {});
      return {
        values: {},
        errors,
      };
    }
    
    return {
      values: {},
      errors: {
        root: {
          type: 'validation',
          message: 'Unknown validation error occurred.',
        },
      },
    };
  }
};
