extern "C" int func_60c717fc(char *p, unsigned idx)
{
    int result = 0;
    if (*(unsigned *)(p + 0x3c) > idx) {
        p[0xfe] = 1;
        unsigned *table = *(unsigned **)(p + 0x48);
        char *elem = (char *)table[idx];
        result = *(int *)(elem + 0xc);
    }
    return result;
}