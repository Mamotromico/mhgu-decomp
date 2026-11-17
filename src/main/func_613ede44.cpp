extern "C" int func_613efc80(int);

extern "C" int func_613ede44(char *p) {
    int r = func_613efc80(*(int *)(p + 0x5d8));
    if (r <= 1)
        r = 1;
    return r;
}