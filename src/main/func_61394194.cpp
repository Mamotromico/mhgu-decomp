extern "C" void func_61394194(char *node)
{
    char *head = node + 0x8;
    char *cur = *(char **)(node + 0xc);
    if (cur == head)
        return;
    do {
        *(void **)(cur + 0xc) = nullptr;
        cur = *(char **)(cur + 0x4);
    } while (cur != head);
}