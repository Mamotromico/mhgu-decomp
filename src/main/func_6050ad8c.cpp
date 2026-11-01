extern "C" int func_6050ad8c(const char *obj) {
    if (*(const int *)(obj + 0x1e4) == 9)
        return 1;
    int r1 = *(const int *)(obj + 0x1e0);
    if (r1 == 9)
        return 1;
    return 0;
}