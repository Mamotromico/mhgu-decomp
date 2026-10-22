struct Src {
    unsigned char pad[0x1f];
    unsigned char flag;
};

struct Pair {
    unsigned int value;
    Src *src;
};

struct Out {
    unsigned int reserved;
    Pair pair;
};

extern "C" int func_60c18548(Out *out, Pair pair) {
    if (pair.src->flag == 0)
        return 0;
    out->pair = pair;
    return 1;
}