module.exports = {
    testEnvironment: 'jsdom',
    moduleNameMapper: {
        '\\.(css|less|scss)$': '<rootDir>/src/__mocks__/styleMock.js',
    '\\.(jpg|jpeg|png|gif|svg)$': '<rootDir>/src/__mocks__/fileMock.js'
    },
    setupFilesAfterEnv: ['<rootDir>/src/setupTests.js'],
    transform: {
      '^.+\\.[jt]sx?$': 'babel-jest',
    }
  };