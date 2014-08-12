#!/usr/bin/env python
import argparse


def main():
    parser = argparse.ArgumentParser(description='Traffic light control system')
    parser.add_argument('--master', '-m', help='Address of master')
    args = parser.parse_args()

    print 'Obeying:', args.master


if __name__ == '__main__':
    main()
