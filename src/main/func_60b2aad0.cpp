extern "C" void func_60b2aad0(char *base, int addend) {
    *(int *)(base + 0x16c) += addend;
    *(int *)(base + 0x170) += 1;
    int *p = (int *)(base + (*(int *)(base + 0x178) << 3));
    *(int *)((char *)p + 0x12c) += addend;
    *(int *)((char *)p + 0x130) += 1;
    *(int *)(base + 0x1dc) = 0;
    *(int *)(base + 0x330) += addend;
    *(unsigned char *)(base + 0xe2) = 0;
}