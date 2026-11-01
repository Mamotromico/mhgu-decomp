extern "C" void func_61394010(char *p) {
    char *head = p + 8;
    char *cur = *(char **)(p + 0xc);
    if (cur == head) return;
    do {
        *(volatile unsigned char *)(cur + 0x2c) = 0;
        cur = *(char **)(cur + 0x4);
    } while (cur != head);
}