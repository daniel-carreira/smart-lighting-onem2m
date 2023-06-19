/*
 * Created on Mon Mar 27 2023
 *
 * Author(s): Rafael Pereira (Rafael_Pereira_2000@hotmail.com)
 *            Carla Mendes (carlasofiamendes@outlook.com) 
 *            Ana Cruz (anacassia.10@hotmail.com) 
 * Copyright (c) 2023 IPLeiria
 */

#include <stdio.h>
#include <string.h>
#include "Utils.h"
#include "sqlite3.h"

#define TRUE 1
#define FALSE 0

extern char DB_MEM[MAX_CONFIG_LINE_LENGTH];

int callback(void *NotUsed, int argc, char **argv, char **azColName) {
    int i;
    for (i = 0; i < argc; i++) {
        printf("%s = %s\n", azColName[i], argv[i] ? argv[i] : "NULL");
    }
    printf("\n");
    return 0;
}

// Define an init function that returns an sqlite3 pointer
sqlite3 *initDatabase(const char* databasename) {
    sqlite3 *db;
    int rc = sqlite3_open_v2((strcmp(DB_MEM, "true") == 0 ? ":memory:" : databasename), &db, SQLITE_OPEN_READWRITE | SQLITE_OPEN_CREATE | SQLITE_OPEN_FULLMUTEX, NULL);
    if (rc != SQLITE_OK) {
        fprintf(stderr, "Cannot open database: %s\n", sqlite3_errmsg(db));
        sqlite3_close(db);
        return NULL;
    }

    sqlite3_busy_timeout(db, 1000);

    return db;
}

short execDatabaseScript(char* query, struct sqlite3 *db, short isCallback) {
    char *err_msg = 0;
    short rc = -1;
    if (isCallback == FALSE) {
        rc = sqlite3_exec(db, query, NULL, NULL, &err_msg);
    } else {
        rc = sqlite3_exec(db, query, callback, NULL, &err_msg);
    }
    if (rc != SQLITE_OK) {
        fprintf(stderr, "SQL error: %s\n", err_msg);
        sqlite3_free(err_msg);
        sqlite3_close(db);
        return FALSE;
    }
    return TRUE;
}

int closeDatabase(sqlite3 *db) {
    int rc;
    sqlite3_stmt *stmt;

    // Finalize all outstanding statements
    while ((stmt = sqlite3_next_stmt(db, NULL)) != NULL) {
        sqlite3_finalize(stmt);
    }

    // Commit or rollback any outstanding transactions
    if (sqlite3_get_autocommit(db) == 0) {
        rc = sqlite3_exec(db, "COMMIT", NULL, NULL, NULL);
        if (rc != SQLITE_OK) {
            sqlite3_exec(db, "ROLLBACK", NULL, NULL, NULL);
        }
    }

    rc = sqlite3_close(db);
    if (rc != SQLITE_OK) {
        fprintf(stderr, "Error closing database: %s\n", sqlite3_errmsg(db));
        return FALSE;
    }
    return TRUE;
}

int begin_transaction(sqlite3 *db) {
    char *errmsg = 0;
    int rc = sqlite3_exec(db, "BEGIN;", 0, 0, &errmsg);

    if (rc != SQLITE_OK) {
        fprintf(stderr, "SQL error: %s\n", errmsg);
        sqlite3_free(errmsg);
        return rc;
    }

    return SQLITE_OK;
}

int commit_transaction(sqlite3 *db) {
    char *errmsg = 0;
    int rc = sqlite3_exec(db, "COMMIT;", 0, 0, &errmsg);

    if (rc != SQLITE_OK) {
        fprintf(stderr, "SQL error: %s\n", errmsg);
        sqlite3_free(errmsg);
        return rc;
    }

    return SQLITE_OK;
}

int rollback_transaction(sqlite3 *db) {
    char *errmsg = 0;
    int rc = sqlite3_exec(db, "ROLLBACK;", 0, 0, &errmsg);

    if (rc != SQLITE_OK) {
        fprintf(stderr, "SQL error: %s\n", errmsg);
        sqlite3_free(errmsg);
        return rc;
    }

    return SQLITE_OK;
}