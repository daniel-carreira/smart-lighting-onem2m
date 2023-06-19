/*
 * Created on Mon Mar 27 2023
 *
 * Author(s): Rafael Pereira (Rafael_Pereira_2000@hotmail.com)
 *            Carla Mendes (carlasofiamendes@outlook.com) 
 *            Ana Cruz (anacassia.10@hotmail.com) 
 * Copyright (c) 2023 IPLeiria
 */

#define MAX_CONFIG_LINE_LENGTH 64  

#define TRUE 1
#define FALSE 0

#include <stdio.h>
#include <time.h>
#include <ctype.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <ctype.h>
#include <pthread.h>
#include <regex.h>

#include "cJSON.h"

typedef struct {
    char* nu;
    char* topic;
    char* body;
} notificationData;


int is_valid_url(const char* url);
char* getCurrentTime();
char* getCurrentTimeLong();
void to_lowercase(char* str);
char* get_datetime_days_later(int days);
void parse_config_line(char* line);
void load_config_file(const char* filename);
void generate_unique_id(char *id_str);
char is_number(const char *str);
int key_in_array(const char *key, const char **key_array, size_t key_array_len);
void remove_unauthorized_chars(char *str);
void* send_notification(void* arg);
// void mqtt_publish(const char* url, const char* topic, const char* message);
void mqtt_publish_message(const char* addr, const char* topic, const char* message);
int send_http_request(const char *base_url, const char *resource_url, const char *content);