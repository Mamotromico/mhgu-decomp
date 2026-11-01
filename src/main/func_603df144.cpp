extern "C" int func_603df144(char *p) {
    int a = *(int *)(p + 4);
    int b;
    if (a != 0) {
        *(int *)(p + 4) = 0;
        b = *(int *)(p + 8) + 1;
        *(int *)(p + 8) = b;
    } else {
        b = *(int *)(p + 8);
    }
    int c = *(int *)(p + 0xc);
    return b - c;
}