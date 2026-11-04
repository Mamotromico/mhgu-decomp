extern "C" int func_60069fc8(char *base, int key)
{
    int *head = (int *)(base + 0x25b4);
    if (*head == key) {
        *head = 0;
        return 1;
    }
    int *tail = (int *)(base + 0x25b8);
    if (*tail == key) {
        *tail = 0;
        return 1;
    }
    return 0;
}