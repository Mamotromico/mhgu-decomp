extern "C" int func_613a7984(char *p) {
    char *head = p + 8;
    char *node = *(char **)(p + 0xc);
    int n = 0;
    while (node != head) {
        node = *(char **)(node + 4);
        n++;
    }
    return n;
}