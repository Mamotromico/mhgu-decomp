struct Node {
    char pad_0[0x40];
    unsigned int value;
};

extern "C" unsigned int func_613ca678(Node *p) {
    return p ? p->value : 0;
}