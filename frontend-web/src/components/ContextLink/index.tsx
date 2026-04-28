/**
 * 上下文跳转链接组件
 * 携带上下文参数的跳转链接
 */
import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from 'antd';
import { ArrowRightOutlined } from '@ant-design/icons';

interface ContextLinkProps {
  to: string;
  context?: Record<string, string>;
  children: React.ReactNode;
  onClick?: () => void;
  button?: boolean;
  type?: 'link' | 'default' | 'primary';
}

export const ContextLink: React.FC<ContextLinkProps> = ({
  to,
  context = {},
  children,
  onClick,
  button = false,
  type = 'link',
}) => {
  // 构建带上下文的 URL
  const buildUrl = () => {
    const params = new URLSearchParams(context);
    const queryString = params.toString();
    return queryString ? `${to}?${queryString}` : to;
  };

  const handleClick = (e: React.MouseEvent) => {
    if (onClick) {
      e.preventDefault();
      onClick();
    }
  };

  if (button) {
    return (
      <Button
        type={type === 'primary' ? 'primary' : 'default'}
        icon={<ArrowRightOutlined />}
        onClick={handleClick}
      >
        <Link to={buildUrl()} className="ant-btn-link-wrapper">
          {children}
        </Link>
      </Button>
    );
  }

  return (
    <Link to={buildUrl()} onClick={handleClick}>
      {children}
    </Link>
  );
};
