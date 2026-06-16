import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      globals: globals.browser,
    },
  },
  {
    files: ['src/**/*.{ts,tsx}'],
    ignores: [
      'src/auth/AuthContext.tsx',
      'src/services/rolesApi.ts',
      'src/auth/ProtectedRoute.tsx',
      'src/auth/usePermissions.ts',
      'src/auth/permissionUtils.ts',
      'src/auth/moduleUtils.ts'
    ],
    rules: {
      'no-restricted-syntax': [
        'error',
        {
          selector: "CallExpression[callee.object.name='localStorage'][callee.property.name='getItem'][arguments.0.value=/^(role|permissions)$/]",
          message: "Do not read 'role' or 'permissions' directly from localStorage. Use the central usePermissions() hook instead."
        },
        {
          selector: "BinaryExpression[left.property.name='role'][right.type='Literal']",
          message: "Do not perform direct role comparisons. Use permission-based gating (can/hasPermission) instead."
        },
        {
          selector: "MemberExpression[object.name='permissions'][property.name='includes']",
          message: "Do not call permissions.includes() directly. Use hasPermission() or can() from usePermissions() instead."
        }
      ]
    }
  }
])
