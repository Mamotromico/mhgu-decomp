extern "C" int func_602b4e94(void *arg0) {
    void *p = *(void **)arg0;
    int (*fn)(void *) = *(int (**)(void *))((char *)p + 0x828);
    int r = fn(arg0);
    unsigned ret = 0;
    if ((unsigned)r < 2)
        ret = 1;
    return ret;
}